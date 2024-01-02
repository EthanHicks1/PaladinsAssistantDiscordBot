from discord import Embed, colour, File
from discord.ext import commands

from arez.exceptions import HTTPException as AHTTPException
from arez.exceptions import NotFound as ANotFound
from arez.player import Player

from PIL import Image, ImageFont, ImageDraw, ImageOps
from io import BytesIO

import my_utils as helper


class MatchCog(commands.Cog, name="Match Command"):
    """Match Cog"""
    def __init__(self, bot):
        self.bot = bot

        self.max_bans = 8

    # Returns an image of a match with player details
    @commands.command(name='match', pass_context=True, ignore_extra=False, aliases=["Match", "mecz", "Mecz"])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def match(self, ctx, player_name_or_match_id, extra_option="-b"):
        lang = await self.bot.command_utils.check_language(ctx=ctx)

        async with ctx.channel.typing():
            # the player has given us a match_id (new way to process)
            if player_name_or_match_id.isdecimal():
                try:
                    match = await self.bot.api.get_match(int(player_name_or_match_id), expand_players=True)
                    win_status = ''
                except (ANotFound, AHTTPException):
                    embed = Embed(
                        title="Match Not Found!",
                        description="Match with the id: `{}` could not be found.".format(player_name_or_match_id),
                        colour=colour.Color.dark_teal()
                    )
                    await ctx.send(embed=embed)
                    return None
            # old way of processing... get the previous match for the player!!!
            else:
                current_player = await self.bot.command_utils.process_name(author_id=ctx.author.id,
                                                                           player_name=player_name_or_match_id)

                if not isinstance(current_player, Player):
                    await ctx.send(embed=await self.bot.command_utils.process_error(error_number=current_player,
                                                                                    player_name=player_name_or_match_id,
                                                                                    lang=lang))
                    return None

                paladins_data = await current_player.get_match_history()
                # Endpoint down
                if paladins_data is None:
                    await helper.log_live_error(bot=self.bot, messages=["Paladins Endpoint down (no data returned)"])
                    await ctx.send("```fix\nPaladins Endpoint down (no data returned). Please try again later and "
                                   "hopefully by then Evil Mojo will have it working again.```")
                    return None

                try:
                    partial_match = paladins_data[0]
                except IndexError:
                    embed = Embed(
                        description="Player does not have recent match data.",
                        colour=colour.Color.dark_teal()
                    )

                    await ctx.send(embed=embed)
                    return None

                win_status = 'Win' if partial_match.winner else 'Loss'

                try:
                    match = await self.bot.api.get_match(partial_match.id, expand_players=True)
                except TypeError as TE:
                    # New error that started occurring in the Paladins API way more at the end of 2023
                    if TE.args[0] == "int() argument must be a string, a bytes-like object or a number, not 'NoneType'":
                        raise ValueError("MalformedMatch", partial_match.id)

            # Process a match and create an image from a match object --------------------------------------------------
            team1_data = []
            team2_data = []
            team1_champs = []
            team2_champs = []
            team1_parties = {}
            team2_parties = {}
            new_party_id = 0
            team1_r, team2_r = [], []
            extra_d1, extra_d2 = [], []

            match_info = [win_status, match.duration.minutes, match.region.name,
                          str(match.map_name), match.score[0], match.score[1]]
            match_queue_id = match.queue.value

            for pd in match.players:
                p = pd.player
                # print(type(p))
                # print(p)
                # player_id = int(p.id)
                # print(pd) no private accounts
                # print(pd.rank.value)
                # print(p.name, p.id)

                # Todo, this ideally should be a function to remove duplicate logic
                if pd.team_number == 1:
                    if p.private:
                        name = "*****"
                        level = pd.account_level  # Can get private player level >_>
                        platform = None
                        extra_d1.append(['', pd.healing_self])
                    else:
                        name = p.name
                        level = p.calculated_level
                        platform = str(p.platform.value)
                        extra_d1.append([name, pd.healing_self])
                    # print(pd.damage_done, pd.damage_bot)
                    team1_data.append([name, level, "{:,}".format(pd.credits), pd.kda_text,
                                       "{:,}".format(pd.damage_done), "{:,}".format(pd.damage_taken),
                                       pd.objective_time, "{:,}".format(pd.shielding),
                                       "{:,}".format(pd.healing_done), pd.party_number, platform,
                                       "{:,}".format(pd.healing_self), pd.loadout.passive])

                    # Todo add in talents
                    # Kinessa is using the Oppression Talent (16387)
                    # https://webcdn.hirezstudios.com/paladins/champion-cards/oppression.jpg
                    if pd.champion and pd.champion.name == 'Kinessa' and \
                            pd.loadout.talent and pd.loadout.talent.name == 'Oppression':
                        team1_champs.append('kinessa_oppression')
                    else:
                        team1_champs.append(pd.champion.name)

                    # Handle combining party numbers into just a single party number
                    if pd.party_number not in team1_parties or pd.party_number == 0:
                        team1_parties[pd.party_number] = ""
                    else:
                        if team1_parties[pd.party_number] == "":
                            new_party_id += 1
                            team1_parties[pd.party_number] = "" + str(new_party_id)
                    # Handle getting player ranks
                    if match_queue_id == 486:
                        if int(p.id) in self.bot.cached_kbm_gm:
                            team1_r.append('27')
                        else:
                            team1_r.append(str(pd.rank.value))
                    else:
                        team1_r.append('-1')
                else:
                    if p.private:
                        name = "*****"
                        level = pd.account_level  # Can get private player level >_>
                        platform = None
                        extra_d2.append(['', pd.healing_self])
                    else:
                        name = p.name
                        level = p.calculated_level
                        platform = str(p.platform.value)
                        extra_d2.append([name, pd.healing_self])
                    team2_data.append([name, level, "{:,}".format(pd.credits), pd.kda_text,
                                       "{:,}".format(pd.damage_done), "{:,}".format(pd.damage_taken),
                                       pd.objective_time, "{:,}".format(pd.shielding),
                                       "{:,}".format(pd.healing_done), pd.party_number, platform,
                                       "{:,}".format(pd.healing_self), pd.loadout.passive])

                    # Kinessa is using the Oppression Talent (16387)
                    # https://webcdn.hirezstudios.com/paladins/champion-cards/oppression.jpg
                    if pd.champion and pd.champion.name == 'Kinessa' and \
                            pd.loadout.talent and pd.loadout.talent.name == 'Oppression':
                        team2_champs.append('kinessa_oppression')
                    else:
                        team2_champs.append(pd.champion.name)

                    # Handle combining party numbers into just a single party number
                    if pd.party_number not in team2_parties or pd.party_number == 0:
                        team2_parties[pd.party_number] = ""
                    else:
                        if team2_parties[pd.party_number] == "":
                            new_party_id += 1
                            team2_parties[pd.party_number] = "" + str(new_party_id)
                    # Handle getting player ranks
                    if match_queue_id == 486:
                        if int(p.id) in self.bot.cached_kbm_gm:
                            team2_r.append('27')
                        else:
                            team2_r.append(str(pd.rank.value))
                    else:
                        team2_r.append('-1')

            # Process extra parameter
            color = True if extra_option == '-c' else False
            detailed = True if extra_option == '-d' else False

            if not match.bans:
                bans = ['', '', '', '', '', '', '', '']
            else:
                bans = []
                for ban in match.bans:
                    if ban:  # They can be null now
                        bans.append(ban.name)
                while len(bans) < self.max_bans:
                    bans.append('')

            buffer = await self.create_history_image(team1_champs, team2_champs, team1_data, team2_data,
                                                     team1_parties, team2_parties, team1_r, team2_r,
                                                     (match_info + bans), color)

            file = File(filename="TeamMatch.png", fp=buffer)
            if not detailed:
                embed = Embed(
                    title="\N{HEAVY BLACK HEART} You are an amazing person! \N{BLUE HEART}",
                    colour=colour.Color.dark_teal()
                )
                await ctx.send(embed=embed, file=file)
            else:
                msg = f'[Match ID:]({match.id})\n\n' \
                      f'#  Player name      Self Healing\n'

                for idx, info in enumerate(extra_d1, start=1):
                    msg += f'{idx}. {info[0]:16} {info[1]}\n'

                msg += '\n'

                for idx, info in enumerate(extra_d2, start=1):
                    msg += f'{idx}. {info[0]:16} {info[1]}\n'

                await ctx.send(file=file)
                await ctx.send(f'```md\n{msg}```')
            return None

    # Creates a match image based on the two teams champions
    async def create_history_image(self, team1, team2, t1_data, t2_data, p1, p2, t1_r, t2_r, match_data, colored):
        shrink = 140
        image_size_y = 512 - shrink * 2
        image_size_x = 512
        offset = 5
        history_image = Image.new('RGB', (image_size_x * 9, image_size_y * 12 + 264))

        # Adds the top key panel
        key = await self.create_player_key_image(image_size_x, image_size_y, colored)
        history_image.paste(key, (0, 0))

        # Creates middle panel
        mid_panel = await self.create_middle_info_panel(match_data)
        history_image.paste(mid_panel, (0, 1392 - 40))

        # Rare case where a player can be completely missing... fill in for list iteration below
        while len(team1) < 5:
            team1.append(None)

        while len(team2) < 5:
            team2.append(None)

        # Adding in player data
        for i, (champ, champ2) in enumerate(zip(team1, team2)):
            if champ is None:
                pass
            else:
                try:
                    champ_image = Image.open("icons/champ_icons/{}.png".format(
                        await helper.convert_champion_name_image(champ)))
                except FileNotFoundError:
                    champ_image = Image.open("icons/champ_cards/temp_card_art.png")

                # print(vars(champ_image))
                # Crop image
                if champ != 'kinessa_oppression':
                    border = (0, shrink, 0, shrink)  # left, up, right, bottom
                    champ_image = ImageOps.crop(champ_image, border)
                # champ_image.show()
                # history_image.paste(champ_image, (0, image_size*i, image_size, image_size*(i+1)))
                player_panel = await self.create_player_stats_image(champ_image, t1_data[i], i, p1, t1_r[i], colored)
                history_image.paste(player_panel, (0, (image_size_y + 10) * i + 132))

            # Second team
            if champ2 is None:
                pass
            else:
                try:
                    champ_image = Image.open("icons/champ_icons/{}.png".format(
                        await helper.convert_champion_name_image(champ2)))
                except FileNotFoundError:
                    champ_image = Image.open("icons/champ_cards/temp_card_art.png")     # lol, fails on crop ---> blank
                border = (0, shrink, 0, shrink)  # left, up, right, bottom
                champ_image = ImageOps.crop(champ_image, border)    # fails silently if image is not 512 by 512

                player_panel = await self.create_player_stats_image(champ_image, t2_data[i], i + offset - 1, p2,
                                                                    t2_r[i], colored)
                history_image.paste(player_panel, (0, image_size_y * (i + offset) + 704))

        # Base speed is: 10 seconds
        history_image = history_image.resize((4608 // 2, 3048 // 2), Image.Resampling.LANCZOS)   # 5 seconds
        # history_image = history_image.resize((4608 // 4, 3048 // 4), Image.Resampling.LANCZOS) # 2.5 secs but bad looking

        # Creates a buffer to store the image in
        final_buffer = BytesIO()

        # Store the pillow image we just created into the buffer with the PNG format
        history_image.save(final_buffer, "png")

        # seek back to the start of the buffer stream
        final_buffer.seek(0)

        return final_buffer

    # Creates the text at the top of the image
    @staticmethod
    async def create_player_key_image(x, y, color=False):
        key = Image.new('RGB', (x * 9, y - 100), color=(112, 225, 225))
        base_draw = ImageDraw.Draw(key)
        # ss = "Player Credits K/D/A  Damage  Taken  Objective Time  Shielding  Healing"
        base_draw.text((20, 0), "Champion", font=ImageFont.truetype("arial", 80), fill=(0, 0, 0))
        base_draw.text((x + 20, 0), "Player", font=ImageFont.truetype("arial", 80), fill=(0, 0, 0))

        # Ranked
        fill = (128, 0, 128) if color else (0, 0, 0)
        base_draw.text((x + 665, 0), "R", font=ImageFont.truetype("arial", 100), fill=fill)

        x += 75
        # Parties
        fill = (128, 0, 128) if color else (0, 0, 0)
        base_draw.text((x + 750, 0), "P", font=ImageFont.truetype("arial", 100), fill=fill)

        # Credits/Gold earned
        fill = (218, 165, 32) if color else (0, 0, 0)
        base_draw.text((x + 900, 0), "Credits", font=ImageFont.truetype("arial", 80), fill=fill)

        # KDA
        fill = (101, 33, 67) if color else (0, 0, 0)
        base_draw.text((x + 1250, 0), "K/D/A", font=ImageFont.truetype("arial", 80), fill=fill)

        # Damage done
        fill = (255, 0, 0) if color else (0, 0, 0)
        base_draw.text((x + 1700, 0), "Damage", font=ImageFont.truetype("arial", 80), fill=fill)

        # Damage taken
        fill = (220, 20, 60) if color else (0, 0, 0)
        base_draw.text((x + 2200, 0), "Taken", font=ImageFont.truetype("arial", 80), fill=fill)

        # Objective time
        fill = (159, 105, 52) if color else (0, 0, 0)
        base_draw.text((x + 2650, 0), "Objective", font=ImageFont.truetype("arial", 60), fill=fill)
        base_draw.text((x + 2700, 60), "Time", font=ImageFont.truetype("arial", 60), fill=fill)

        # Shielding
        fill = (0, 51, 102) if color else (0, 0, 0)
        base_draw.text((x + 3000, 0), "Shielding", font=ImageFont.truetype("arial", 80), fill=fill)

        # Healing
        fill = (0, 128, 0) if color else (0, 0, 0)
        base_draw.text((x + 3500, 0), "Healing", font=ImageFont.truetype("arial", 80), fill=fill)

        return key

    @staticmethod
    async def create_middle_info_panel(md):
        middle_panel = Image.new('RGB', (512 * 9, 512), color=(217, 247, 247))

        # Adding in map to image
        map_name = map_file_name = (
            md[3].strip().replace("Ranked ", "").replace(" (TDM)", "").replace(" (Onslaught)", "")
            .replace(" (Siege)", "")).replace("Practice ", "")
        if "WIP" in map_name:
            map_file_name = "test_maps"
            map_name = map_name.replace("WIP ", "")

        # Needed to catch weird-unknown map modes
        try:
            match_map = Image.open("icons/maps/{}.png".format(map_file_name.lower().replace(" ", "_").replace("'", "")
                                                              .replace("_(koth)", "")))
        except FileNotFoundError:
            match_map = Image.open("icons/maps/test_maps.png")

        match_map = match_map.resize((512 * 2, 512), Image.Resampling.LANCZOS)
        middle_panel.paste(match_map, (0, 0))

        # Preparing the panel to draw on
        draw_panel = ImageDraw.Draw(middle_panel)

        # Add in match information
        ds = 50  # Down Shift
        rs = 20  # Right Shift
        rs_offset = int(512 * 6.9)  # Right Shift offset
        draw_panel.text((512 * 2 + rs, 0 + ds), str(md[0]), font=ImageFont.truetype("arial", 100), fill=(0, 0, 0))
        draw_panel.text((512 * 2 + rs, 100 + ds), (str(md[1]) + " minutes"), font=ImageFont.truetype("arial", 100),
                        fill=(0, 0, 0))
        draw_panel.text((512 * 2 + rs, 200 + ds), str(md[2]), font=ImageFont.truetype("arial", 100), fill=(0, 0, 0))
        draw_panel.text((512 * 2 + rs, 300 + ds), str(map_name), font=ImageFont.truetype("arial", 100), fill=(0, 0, 0))

        # If it's siege or ranked show the score
        if md[4] <= 4 and md[5] <= 4:
            # Right shift
            rs = 100

            # Team 1
            draw_panel.text((512 * 4 + rs, ds), "Team 1 Score: ", font=ImageFont.truetype("arial", 100), fill=(0, 0, 0))
            draw_panel.text((512 * 4 + rs * 8, ds), str(md[4]), font=ImageFont.truetype("arialbd", 100), fill=(0, 0, 0))

            center = (512 / 2 - 130 / 2)
            # VS
            draw_panel.text((512 * 5 - 150, center), "VS", font=ImageFont.truetype("arialbd", 130), fill=(0, 0, 0))

            # Team 2
            draw_panel.text((512 * 4 + rs, 372), "Team 2 Score: ", font=ImageFont.truetype("arial", 100), fill=(0, 0, 0))
            draw_panel.text((512 * 4 + rs * 8, 372), str(md[5]), font=ImageFont.truetype("arialbd", 100), fill=(0, 0, 0))

        #  add in banned champs if it's a ranked match
        if md[6]:
            center2 = (512 / 2 - 80 / 2)
            # Ranked bans
            draw_panel.text((512 * 5 + rs * 8, center2), "Bans:", font=ImageFont.truetype("arialbd", 80),
                            fill=(0, 0, 0))

            # Team 1 Bans
            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(str(md[6]))))
                champ_image = champ_image.resize((200, 200))
                middle_panel.paste(champ_image, (rs_offset + rs, ds))
            except FileNotFoundError:
                pass

            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(str(md[7]))))
                champ_image = champ_image.resize((200, 200))
                middle_panel.paste(champ_image, (rs_offset + rs + 240, ds))
            except FileNotFoundError:
                pass

            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(str(md[8]))))
                champ_image = champ_image.resize((200, 200))
                middle_panel.paste(champ_image, (rs_offset + rs + 240 * 2, ds))
            except FileNotFoundError:
                pass

            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(str(md[9]))))
                champ_image = champ_image.resize((200, 200))
                middle_panel.paste(champ_image, (rs_offset + rs + 240 * 3, ds))
            except FileNotFoundError:
                pass

            # Team 2 Bans
            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(str(md[10]))))
                champ_image = champ_image.resize((200, 200))
                middle_panel.paste(champ_image, (rs_offset + rs, ds + 232))
            except FileNotFoundError:
                pass

            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(str(md[11]))))
                champ_image = champ_image.resize((200, 200))
                middle_panel.paste(champ_image, (rs_offset + rs + 240, ds + 232))
            except FileNotFoundError:
                pass

            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(str(md[12]))))
                champ_image = champ_image.resize((200, 200))
                middle_panel.paste(champ_image, (rs_offset + rs + 240 * 2, ds + 232))
            except FileNotFoundError:
                pass

            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(str(md[13]))))
                champ_image = champ_image.resize((200, 200))
                middle_panel.paste(champ_image, (rs_offset + rs + 240 * 3, ds + 232))
            except FileNotFoundError:
                pass

        return middle_panel

    @staticmethod
    async def create_player_stats_image(champ_icon, champ_stats, index, party, rank, color=False):
        shrink = 140
        offset = 10
        image_size_y = 512 - shrink * 2
        img_x = 512
        middle = image_size_y / 2 - 50
        im_color = (175, 238, 238, 0) if index % 2 == 0 else (196, 242, 242, 0)
        # color = (175, 238, 238)   # light blue
        # color = (196, 242, 242)   # lighter blue

        # Something changed in the PILLOW library going from 6.2.1 to 8.2.0 which now requires this to also be `RGB`
        # instead of `RGBA` 5/15/2021
        champ_stats_image = Image.new('RGB', (img_x * 9, image_size_y + offset * 2), color=im_color)

        oppressed = False
        if hasattr(champ_icon, 'filename') and 'kinessa_oppression' in champ_icon.filename:
            champ_stats_image.paste(champ_icon, (offset, offset), champ_icon)
            oppressed = True
            # let's add some more of the icons on lol
            champ_stats_image.paste(champ_icon, (img_x + 3200, int(middle) - 55), champ_icon)
            champ_stats_image.paste(champ_icon, (img_x + 3650, int(middle) - 55), champ_icon)
            champ_stats_image.paste(champ_icon, (img_x + 3850, int(middle) - 55), champ_icon)
        else:
            champ_stats_image.paste(champ_icon, (offset, offset))

        if rank != '-1':
            scale = 1.5
            rank = Image.open("icons/ranks/{}.png".format(rank))
            width, height = rank.size
            rank = rank.resize((int(width * scale), int(height * scale)))
            champ_stats_image.paste(rank, (img_x + 600, offset), rank)

        # Handle Octavia (2540) Passive
        passive = champ_stats[12]
        if passive:
            try:
                passive_icon = Image.open(f"icons/passives/{passive.name}.png")
                champ_stats_image.paste(passive_icon, (img_x - 150, offset), passive_icon)
            except FileNotFoundError:
                pass

        platform = champ_stats[10]
        if platform == "XboxLive" or platform == '10':
            platform_logo = Image.open("icons/platforms/xbox_logo.png").resize((100, 100), Image.Resampling.LANCZOS)
            platform_logo = platform_logo.convert("RGBA")
            champ_stats_image.paste(platform_logo, (img_x + 225, int(middle) + 60), platform_logo)
        elif platform == "Nintendo Switch" or platform == '22':
            platform_logo = Image.open("icons/platforms/switch_logo.png")
            width, height = platform_logo.size
            scale = .15
            platform_logo = platform_logo.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)
            platform_logo = platform_logo.convert("RGBA")
            champ_stats_image.paste(platform_logo, (img_x + 185, int(middle) + 45), platform_logo)
        elif platform == "PSN" or platform == '9':
            platform_logo = Image.open("icons/platforms/ps4_logo.png").resize((100, 100), Image.Resampling.LANCZOS)
            platform_logo = platform_logo.convert("RGBA")
            champ_stats_image.paste(platform_logo, (img_x + 225, int(middle) + 60), platform_logo)

        base_draw = ImageDraw.Draw(champ_stats_image)

        # The oppressor
        if oppressed:
            fill = (255, 0, 0)
            base_draw.text((img_x - 200, middle + 25), 'the oppressor', font=ImageFont.truetype("arialbd", 75),
                           fill=fill)

        # Private account or unknown
        if str(champ_stats[0]) == "":
            champ_stats[0] = "*****"

        # Player name and champion level
        font = ImageFont.truetype("arialbd", 80)
        width = font.getlength(str(champ_stats[0]))
        max_width = 590
        if width > max_width:
            font_size = int(80 / (width/max_width))
        else:
            font_size = 80

        base_draw.text((img_x + 20, middle - 40), str(champ_stats[0]), font=ImageFont.truetype("arialbd", font_size),
                       fill=(0, 0, 0))
        base_draw.text((img_x + 20, middle + 60), str(champ_stats[1]), font=ImageFont.truetype("arial", 80),
                       fill=(0, 0, 0))

        # shift right to allow for room for added in player rank for ranked matches
        img_x += 75

        # Parties
        fill = (128, 0, 128) if color else (0, 0, 0)
        base_draw.text((img_x + 750, middle), party[champ_stats[9]], font=ImageFont.truetype("arial", 100), fill=fill)

        # Credits/Gold earned
        fill = (218, 165, 32) if color else (0, 0, 0)
        base_draw.text((img_x + 900, middle), str(champ_stats[2]), font=ImageFont.truetype("arial", 100), fill=fill)

        # KDA
        fill = (101, 33, 67) if color else (0, 0, 0)
        base_draw.text((img_x + 1250, middle), str(champ_stats[3]), font=ImageFont.truetype("arial", 100), fill=fill)

        # Damage done
        fill = (255, 0, 0) if color else (0, 0, 0)
        base_draw.text((img_x + 1700, middle), str(champ_stats[4]), font=ImageFont.truetype("arial", 100), fill=fill)

        # Damage taken
        fill = (220, 20, 60) if color else (0, 0, 0)
        base_draw.text((img_x + 2200, middle), str(champ_stats[5]), font=ImageFont.truetype("arial", 100), fill=fill)

        # Objective time
        fill = (159, 105, 52) if color else (0, 0, 0)
        base_draw.text((img_x + 2700, middle), str(champ_stats[6]), font=ImageFont.truetype("arial", 100), fill=fill)

        # Shielding
        fill = (0, 51, 102) if color else (0, 0, 0)
        base_draw.text((img_x + 3000, middle), str(champ_stats[7]), font=ImageFont.truetype("arial", 100), fill=fill)

        # Healing
        fill = (0, 128, 0) if color else (0, 0, 0)
        base_draw.text((img_x + 3500, middle), str(champ_stats[8]), font=ImageFont.truetype("arial", 100), fill=fill)

        # Self Healing # ToDo add this in
        # fill = (0, 128, 0) if color else (0, 0, 0)
        # base_draw.text((img_x + 3700, middle), str(champ_stats[11]), font=ImageFont.truetype("arial", 50), fill=fill)

        # champ_stats_image.show()

        return champ_stats_image


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(MatchCog(bot))
