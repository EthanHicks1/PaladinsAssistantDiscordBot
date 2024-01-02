from discord.ext import commands
from discord import File, Embed, colour
from arez.player import Player
from arez import Language

from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import textwrap
import my_utils as helper
import asyncio
import time

# Built in discord UI
from discord import SelectOption, Interaction
from discord.errors import HTTPException
from discord.ui import Select

from MyCustomDiscordView import MyGenericView


class Decks(commands.Cog, name="Decks Command"):
    """
    Decks Cog
    This isn't worth maintaining as the API continues to break.
    """
    def __init__(self, bot):
        self.bot = bot

    class DeckSelect(Select):
        def __init__(self, *args, **kwargs):
            self.deck_raw = kwargs.pop('deck_raw')
            self.champ_name = kwargs.pop('champ_name')
            self.ctx = kwargs.pop('ctx')
            self.parent = kwargs.pop('parent')
            super().__init__(*args, **kwargs)

        async def callback(self, interaction: Interaction):
            current_selection = int(self.values[0])
            # print(self.deck_raw)
            # Update message to remove selected option
            try:
                target_deck = self.deck_raw.pop(current_selection)  # self.deck_raw[current_selection]
                # bug_selection_history.append(current_selection)
            except KeyError:
                # Try to update the view to remove the invalid option
                await interaction.response.send_message("Discord had an issue with processing your selection. "
                                                        "Please try again shortly :(", view=self.view)
                '''await helper.log_live_error(bot=self.bot,
                                            messages=[f'Selection {current_selection}.'
                                                      f'\n Decks are currently', deck_raw,
                                                      f'\n Selection history: {bug_selection_history}'])'''
                return

            # Create and send the image
            buffer = await self.parent.create_deck_image(self.champ_name, target_deck)
            file = File(filename="Deck.png", fp=buffer)

            await self.ctx.send(file=file)

            my_select = self.view.children[0]
            if isinstance(my_select, Select):
                if len(my_select.options) > 1:
                    # Reconstruct decks
                    new_deck_list = []
                    for key, value in self.deck_raw.items():
                        if value.name:
                            new_deck_list.append(SelectOption(label=value.name, value=str(key)))
                        else:
                            new_deck_list.append(SelectOption(label=f'{value.champion.name} {key}', value=str(key)))

                    my_select.options = new_deck_list

                    ''' found = False
                    for option in my_select.options:
                        if found:
                            option.value = int(option.value) - 1
                        else:
                            if option.value == current_selection:
                                print("Found the target", option.value)
                                found = True
                                my_select.options.pop(int(current_selection))'''
                else:
                    my_select.disabled = True
                    try:
                        await interaction.response.edit_message(content="Out of Decks!", view=self.view)
                        return
                    except HTTPException:
                        pass

            # Looks like this can fail but still can edit the view >_>
            try:
                await interaction.response.edit_message(view=self.view)
            except HTTPException:
                pass

            # await interaction.response.send_message(file=file)
            # await interaction.response.send_message(f"You selected {current_selection}", view=self.view)

    @commands.command(name='deck', pass_context=True,
                      aliases=["Deck", "decks", "Decks", "talia", "Talia", 'baralho', 'baralhos'], ignore_extra=False)
    @commands.cooldown(4, 30, commands.BucketType.user)
    async def deck(self, ctx, player_name, champ_name):
        # Lol, this permission means nothing on a bot
        # if not ctx.channel.permissions_for(ctx.me).use_slash_commands:
        #    raise ValueError("MissingSlashPerms", None)

        # ToDo: 1. Let users select a talent from list to add to their image [drop down]
        # ToDo: 2. Let users select from list multiple saved header/banner images [drop down]

        lang = await self.bot.command_utils.check_language(ctx=ctx)

        current_player = await self.bot.command_utils.process_name(author_id=ctx.author.id, player_name=player_name)

        if not isinstance(current_player, Player):
            await ctx.send(embed=await self.bot.command_utils.process_error(error_number=current_player,
                                                                            player_name=player_name,
                                                                            lang=lang))
            return None

        original_name = champ_name
        champ_name = await helper.process_champion_name(champ_name)
        if not champ_name:
            raise ValueError("InvalidChampName", original_name)

        async with ctx.channel.typing():
            player_decks = await current_player.get_loadouts(language=Language(lang))

            deck_list = []
            deck_raw = {}
            # bug_selection_history = []

            if 'Mal' in champ_name:  # lame...
                champ_name = "Mal'Damba"

            idx = 0
            for loadout in player_decks:
                if loadout.champion.name == champ_name:
                    if loadout.name:
                        deck_list.append(SelectOption(label=loadout.name, value=str(idx)))
                    else:
                        deck_list.append(SelectOption(label=f'{loadout.champion.name} {idx}', value=str(idx)))

                    deck_raw[idx] = loadout
                    idx += 1

            # They did not have any decks for the current champion
            if not deck_list:
                embed = Embed(
                    title=f'\N{WARNING SIGN} No Custom Decks. \N{WARNING SIGN}',
                    description=f'Create a custom deck for **`{champ_name}`** for option(s) to show up here.',
                    colour=colour.Color.red()
                )
                await ctx.send(embed=embed)
                return None

            # Command Vars
            comp_timeout = 60

            view_ui = MyGenericView(timeout=comp_timeout, author=ctx.author)
            rand_menu = self.DeckSelect(options=deck_list, placeholder="Select a deck", custom_id="DecKMenu",
                                        deck_raw=deck_raw, champ_name=champ_name, ctx=ctx, parent=self)
            view_ui.add_item(rand_menu)
            view_ui.message = await ctx.send(f'This message will self destruct in {comp_timeout} seconds.',
                                             view=view_ui)

    # Creates a image desks
    @classmethod
    async def create_deck_image(cls, champ_name, deck):
        """
        Creates an image for a deck.
        Update 1/1/2024 --> The Paladins API now doesn't return description for a lot of cards. Nice
        """
        champ_id = deck.champion.id
        player_name = deck.player.name
        card_image_x = 314
        card_image_y = 479

        # Main image
        color = (0, 0, 0, 0)
        deck_image = Image.new('RGBA', (1570, 800), color=color)

        champ_name = await helper.convert_champion_name_image(champ_name)
        champ_header = f'icons/champ_headers/{champ_name}.png'
        try:
            champ_background = Image.open(champ_header).convert('RGBA')
        except FileNotFoundError:
            # print("Could find the file for:", champ_header)
            champ_background = Image.open("icons/maps/test_maps.png").convert('RGBA')
        champ_background = champ_background.resize((1570, 800), Image.Resampling.LANCZOS)
        deck_image.paste(champ_background, (0, 0))

        # Loop to add all the cards in
        for i, card in enumerate(deck.cards):
            # Opens the image of the card
            try:
                card_icon_image = Image.open("icons/champ_cards/{}/{}.png".format(champ_id, card.card.id))
            except FileNotFoundError:
                card_icon_image = Image.open("icons/champ_cards/temp_card_art.png")

            try:    # On a new champion, this can be completely missing from the data
                cool = card.card.cooldown
            except AttributeError:
                cool = 0
            info = [card.card.name, card.points, cool, card.description()]
            card_icon = await cls.create_card_image(card_icon_image, info)

            card_icon = Image.open(card_icon)
            deck_image.paste(card_icon, (card_image_x * i, 800 - card_image_y), card_icon)

        color = (255, 255, 255)

        champ_name = champ_name.upper()

        # Adding in other text on image
        draw = ImageDraw.Draw(deck_image)
        draw.text((0, 0), str(player_name), color, font=ImageFont.truetype("arial", 64))
        draw.text((0, 64), str(champ_name), color, font=ImageFont.truetype("arial", 64))
        if deck.name != 'New Loadout':
            draw.text((0, 128), str(deck.name), color, font=ImageFont.truetype("arial", 64))

        # Creates a buffer to store the image in
        final_buffer = BytesIO()

        # Store the pillow image we just created into the buffer with the PNG format
        deck_image.save(final_buffer, "png")

        # seek back to the start of the buffer stream
        final_buffer.seek(0)

        return final_buffer

    @classmethod
    async def create_card_image(cls, card_image, card_info):
        image_size_x = 256
        image_size_y = 196
        x_offset = 28
        y_offset = 48

        champ_card_name = card_info[0]
        champ_card_level = card_info[1]
        cool_down = card_info[2]
        desc = card_info[3]

        # Load in the Frame image from the web
        card_frame = Image.open("icons/card_frames/{}.png".format(champ_card_level))
        frame_x, frame_y = card_frame.size

        # Create the image without any text (just frame and card image)
        image_base = Image.new('RGBA', (frame_x, frame_y), (0, 0, 0, 0))

        # Resizing images that don't match the common image size
        check_x, check_y = card_image.size
        if check_x != image_size_x or check_y != image_size_y:
            card_image = card_image.resize((image_size_x, image_size_y), Image.Resampling.LANCZOS)

        image_base.paste(card_image, (x_offset, y_offset, image_size_x + x_offset, image_size_y + y_offset))
        image_base.paste(card_frame, (0, 0), card_frame)

        # Add in the Card Number
        draw = ImageDraw.Draw(image_base)
        draw.text((30, frame_y - 56), str(champ_card_level), font=ImageFont.truetype("arialbd", 44))

        # Add card name
        draw = ImageDraw.Draw(image_base)
        font = ImageFont.truetype("arialbd", 21)
        bbox = draw.textbbox(xy=(0, 0), text=champ_card_name, font=font)
        draw.text(((frame_x - bbox[2]) / 2, (frame_y - bbox[3]) / 2 + 20), champ_card_name, font=font)

        # Add card text
        draw = ImageDraw.Draw(image_base)
        font = ImageFont.truetype("arial", 18)
        lines = textwrap.wrap(desc, width=26)
        padding = 40
        for line in lines:
            bbox = draw.textbbox(xy=(0, 0), text=line, font=font)
            draw.text(((frame_x - bbox[2]) / 2, (frame_y - bbox[3]) / 2 + padding + 20), line, font=font,
                      fill=(64, 64, 64))
            padding += 25

        # Add in cool down if needed
        if cool_down != 0:
            # add in number
            draw = ImageDraw.Draw(image_base)
            draw.text((int(frame_x / 2) + 2, frame_y - 66), str(cool_down), font=ImageFont.truetype("arial", 30),
                      fill=(64, 64, 64))

            cool_down_icon = Image.open("icons/champ_cards/cool_down_icon.png")
            image_base.paste(cool_down_icon, (int(frame_x / 2) - 20, frame_y - 60), mask=cool_down_icon)

        # Final image saving steps
        # Creates a buffer to store the image in
        final_buffer = BytesIO()

        # Store the pillow image we just created into the buffer with the PNG format
        image_base.save(final_buffer, "png")

        # seek back to the start of the buffer stream
        final_buffer.seek(0)

        return final_buffer

    # Converts the language to prefix
    @staticmethod
    async def convert_language(x):
        return {
            "en": 1,  # English
            "de": 2,  # German
            "fr": 3,  # French
            "zh": 5,  # Chinese
            "od": 7,  # Out-dated/Unused
            "es": 9,  # Spanish
            "pt": 10,  # Portuguese
            "ru": 11,  # Russian
            "pl": 12,  # Polish
            "tr": 13,  # Turkish
        }.get(x, 1)  # Return English by default if an unknown number is entered


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(Decks(bot))
