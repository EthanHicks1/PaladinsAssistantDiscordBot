from discord.errors import HTTPException as DiscordHTTPException
from discord.errors import NotFound as DiscordNotFound
from discord.errors import Forbidden

from discord import Embed, colour
from discord.ext import commands

from arez.exceptions import NotFound, Private, Unavailable, HTTPException
from arez import Platform as ARezPlatform
from arez.player import Player

import json

# Built in discord UI
from discord import ButtonStyle, Interaction
from discord.ui import Button

from MyCustomDiscordView import MyGenericView


class CommandUtils(commands.Cog):
    """This cog class holds "util" like functions/commands used in the bot."""

    def __init__(self, bot):
        self.bot = bot

        self.id_cache = "cache/discord_id_to_paladins_id.json"
        self.id_cache2 = "cache/discord_id_to_paladins_id2.json"
        self.id_cache3 = "cache/discord_id_to_paladins_id3.json"

    async def get_msg_from_server(self, server_id, channel_id, msg_id, is_pc=True):
        server_id = int(server_id)
        channel_id = int(channel_id)
        msg_id = int(msg_id)

        server = self.bot.get_guild(server_id)
        if server:
            channel = server.get_channel(channel_id)
            if channel:
                try:
                    msg = await channel.fetch_message(msg_id)
                    return msg
                except DiscordNotFound:  # The specified message was not found.
                    try:
                        await channel.send('Could not find the GM Leaderboard in this channel. '
                                           'This likely means the message was deleted.')
                    except Forbidden:
                        print("The server: {} does not have valid permissions set up. #DiscordNotFound"
                              .format(server_id))
                        pass
                except Forbidden:        # You do not have the permissions required to get a message.
                    try:
                        await channel.send('I don\'t not have permission to access the GM leaderboard message.')
                    except Forbidden:
                        print("The server: {} does not have valid permissions set up. #Forbidden"
                              .format(server_id))
                except DiscordHTTPException:    # Retrieving the message failed.
                    try:
                        await channel.send('Failed to fetch the message from Discord.')
                    except Forbidden:
                        print("The server: {} does not have valid permissions set up. #DiscordHTTPException"
                              .format(server_id))
            else:
                pass
        else:
            pass
        # Invalid msg, remove from the internal cache
        self.update_stored_messages(server_id, channel_id, msg_id, is_pc=is_pc, add=False)
        return None

    def update_stored_messages(self, server_id, channel_id, msg_id, is_pc=True, add=True):
        server_id = str(server_id)
        file_loc = self.bot.gm_lb_cache_pc if is_pc else self.bot.gm_lb_cache_con
        with open(file_loc) as json_f:
            gm_lb = json.load(json_f)
            if add:
                gm_lb[server_id] = '{}:{}'.format(channel_id, msg_id)
            else:
                gm_lb.pop(server_id)

        with open(file_loc, 'w') as json_f:
            json.dump(gm_lb, json_f)

    # Checking for is_on_mobile() status
    async def get_mobile_status(self, ctx):
        mobile_status = False
        if ctx.guild is None:  # In DM's
            for guild in self.bot.guilds:
                member = guild.get_member(ctx.author.id)
                if member is not None:
                    mobile_status = member.is_on_mobile()
        else:
            mobile_status = ctx.author.is_on_mobile()
        return mobile_status

    # function used outside of this class to determine the language that a command needs to return
    async def check_language(self, ctx):
        if ctx.guild is None:  # DM to the bot will not have guild.id
            return "en"
        guild_id = str(ctx.guild.id)
        if guild_id in self.bot.servers_config and "lang" in self.bot.servers_config[guild_id]:
            return self.bot.servers_config[guild_id]["lang"]
        else:  # default
            return "en"

    class RemoveAccountButton(Button):
        def __init__(self, *args, **kwargs):
            self.parent = kwargs.pop('parent')
            # self.parent = kwargs.pop('parent', None)  # Prevents key error, but we always need a parent here
            super().__init__(*args, **kwargs)

        async def callback(self, interaction: Interaction):
            # remove the account ---------------------------------------------------------------------------
            cache_file_name = await self.parent.get_cache_file(cache_name=self.custom_id)

            # Change which file we look in
            with open(cache_file_name) as json_f:
                player_discord_ids = json.load(json_f)

            # Should never fail since the button will only exist if the name was already in this file
            player_discord_ids.pop(str(interaction.user.id))

            # need to update the file now
            with open(cache_file_name, 'w') as json_f:
                json.dump(player_discord_ids, json_f)

            target_index = {
                'me': 0,
                'me2': 1,
                'me3': 2,
            }.get(self.custom_id, -1)

            # Update the button
            if target_index != -1:  # shouldn't ever happen
                (self.view.children[target_index]).style = ButtonStyle.grey
                (self.view.children[target_index]).disabled = True
                (self.view.children[target_index]).emoji = None

                await interaction.response.edit_message(view=self.view)

    # Removes a player name from the stored bot file
    @commands.command(name='unstore', pass_context=True, ignore_extra=False)
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def remove_player_name(self, ctx):
        valid_accounts = 0

        # Grab accounts
        player = await self.process_name(author_id=ctx.author.id, player_name='me')
        player2 = await self.process_name(author_id=ctx.author.id, player_name='me2')
        player3 = await self.process_name(author_id=ctx.author.id, player_name='me3')

        view_ui = MyGenericView(timeout=60, author=ctx.author)

        # Add in buttons if valid
        if isinstance(player, Player):
            view_ui.add_item(self.RemoveAccountButton(style=ButtonStyle.red,
                                                      label=f'me → {player.name} ({player.level})',
                                                      emoji='🗑️', custom_id='me', parent=self))
            valid_accounts += 1
        else:
            view_ui.add_item(Button(style=ButtonStyle.grey, label=f'me → No Account Stored', disabled=True))

        if isinstance(player2, Player):
            view_ui.add_item(self.RemoveAccountButton(style=ButtonStyle.red,
                                                      label=f'me2 → {player2.name} ({player2.level})',
                                                      emoji='🗑️', custom_id='me2', parent=self))
            valid_accounts += 1
        else:
            view_ui.add_item(Button(style=ButtonStyle.grey, label=f'me2 → No Account Stored', disabled=True))

        if isinstance(player3, Player):
            view_ui.add_item(self.RemoveAccountButton(style=ButtonStyle.red,
                                                      label=f'me3 → {player3.name} ({player3.level})',
                                                      emoji='🗑️', custom_id='me3', parent=self))
            valid_accounts += 1
        else:
            view_ui.add_item(Button(style=ButtonStyle.grey, label=f'me3 → No Account Stored', disabled=True))

        # Show user options based on how many valid accounts they have stored
        if valid_accounts == 0:
            warning_embed = Embed(
                title="\N{WARNING SIGN} " + 'No Accounts Stored!' + " \N{WARNING SIGN}",
                description='To store an account use the `>>store` command.',
                colour=colour.Color.orange(),
            )
            await ctx.send(embed=warning_embed, delete_after=30)
        else:
            view_ui.message = await ctx.send("```fix\nPressing a button below will remove an account from the bot:```",
                                             view=view_ui)

    # Stores Player's IGN for the bot to use
    @commands.command(name='store', pass_context=True, ignore_extra=False,
                      aliases=["zapisz", "Zapisz", "Store", 'salva'])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def store_player_name(self, ctx, player_name, player_account='me'):
        lang = await self.check_language(ctx=ctx)

        if player_account not in ['me', 'me2', 'me3']:
            embed = Embed(
                title="\N{WARNING SIGN} Invalid option! \N{WARNING SIGN}",
                description=f'```md\n# "{player_account}" should be one of the following options:\n'
                            f'1. me\n2. me2\n3. me3```',
                colour=colour.Color.red()
            )
            await ctx.send(embed=embed)
            return None
        # Console player has entered in their number
        if str(player_name).isdecimal():
            player_id = int(player_name)
        else:  # Try to look up player_name
            player_id = await self.get_player_id(player_name=player_name)

        if player_id > 0:
            cache_file_name = await self.get_cache_file(cache_name=player_account)
            with open(cache_file_name) as json_f:
                player_discord_ids = json.load(json_f)

            player_discord_ids.update({str(ctx.author.id): player_id})  # update dict

            # need to update the file now
            # print("Stored a IGN in conversion dictionary: " + player_name)
            with open(cache_file_name, 'w') as json_f:
                json.dump(player_discord_ids, json_f)
            # await ctx.send("Your Paladin's IGN is now stored as `" + player_name +
            #               "`. You can now use the keyword `me` instead of typing out your name")
            # Todo this command shouldn't be spammed so we should be look up and make sure they are providing a valid
            # name and therefor can sub in their name into the message below to give them a better example
            store_embed = Embed(
                title="\N{WHITE HEAVY CHECK MARK} Your Paladin's IGN is now stored as {} "
                      "\N{WHITE HEAVY CHECK MARK}".format(player_name),
                description=f"You can now use the keyword `{player_account}` instead of typing out your name for "
                            f"commands.\n"
                            "For example if your Paladins IGN is `ZombieKiller`, instead of typing "
                            f"```>>stats ZombieKiller``` you can now do ```>>stats {player_account}```",
                colour=colour.Color.dark_teal()
            )
            await ctx.send(embed=store_embed)
        else:
            await ctx.send(embed=await self.process_error(error_number=player_id, player_name=player_name, lang=lang))

    async def process_error(self, error_number, player_name, lang):
        if error_number == -1:
            title_text = self.bot.cmd_lang_dict["general_error2"][lang].format(player_name)
        elif error_number == -2:
            embed = Embed(
                title="🔒 Private Account 🔒",
                description=self.bot.cmd_lang_dict["general_error"][lang].format('**`' + player_name + '`**'),
                colour=colour.Color.red()
            )
            return embed
        elif error_number == -3:
            title_text = "Hi-Rez API is down. No data is being returned. Try again in a few hours."
        elif error_number == -4:
            title_text = "```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch\n4. Epic```"
        elif error_number == -5:
            title_text = "Name overlap detected. Please look up your Paladins ID using the `>>search` command."
        elif error_number == -7:
            des_text = "You likely entered a special character like `*`. If your name contains special " \
                       "character(s) please look up your `player id` from `Paladins Guru`. This is the number " \
                       "in front of your name on their site once you find your account. If you still need help, feel " \
                       "free to ask for help in the official bot support server: https://discord.gg/njT6zDE"
            embed = Embed(
                title="\N{WARNING SIGN} Special character(s) detected!!! \N{WARNING SIGN}",
                description=des_text,
                colour=colour.Color.red()
            )
            return embed
        elif error_number == -6:
            embed = Embed(
                title="\N{WARNING SIGN} You have not stored your Paladin's In Game Name (IGN) yet. \N{WARNING SIGN}",
                description="To do so please use the store command like so:`>>store Your_Paladin's_IGN`.\n\n"
                            "For example for if your Paladin's IGN is `ZombieKiller`, you would do: "
                            "```>>store ZombieKiller```\nIf you are a **`console player`** you need to provide your "
                            "platform as well surrounded in quotes. For example a `switch` player with the IGN "
                            "`Dark Knight` would do: ```>>store \"Dark Knight switch\"```",
                colour=colour.Color.red()
            )
            return embed
        else:
            # print(error_number)
            title_text = "Unknown error searching for player {}.".format(player_name)

        embed = Embed(
            title=title_text,
            colour=colour.Color.red()
        )
        return embed

    async def process_name(self, author_id, player_name):
        """
        Will attempt to process a player's name into an aRez [Player] so stats can be received from it.
        If it fails, it will return an error as an INT
        """

        # Maybe convert the player name
        if str(player_name) in ['me', 'me2', 'me3']:
            player_name = await self.check_player_name(str(author_id), str(player_name))
        # 99% that someone has been mentioned
        elif player_name[0] == "<" and player_name[1] == "@":
            player_name = player_name.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            if len(player_name) == 18:  # Should only search on someone's "main" account if they are @ed
                player_name = await self.check_player_name(player_name, 'me')
        # Someone is trying to look up a player based on their discord id
        elif player_name.isdecimal() and len(player_name) == 18:
            player_name = await self.check_player_name(player_name, 'me')  # search for player's main account

        # Someone used the keyword me without storing their name
        if player_name is None:
            return -6
        elif isinstance(player_name, Player):
            return player_name
        elif str(player_name).isnumeric():  # player_id was stored in cache
            try:
                player = await self.bot.api.get_player(player=int(player_name))
                full_player = await player
                return full_player
            except NotFound:
                return -1
            except Private:
                return -2
            except Unavailable:
                return -3
            except HTTPException:
                return -7
        else:   # un-stored name
            return await self.get_player_account(player_name=player_name)

    async def check_player_name(self, player_discord_id: str, cache_name: str):
        """
        Converts a discord id into a Paladins ID if stored in the cache.
        input: discord_id
        returns: paladins_id or None
        """

        cache_file_name = await self.get_cache_file(cache_name=cache_name)

        # Change which file we look in
        with open(cache_file_name) as json_f:
            player_discord_ids = json.load(json_f)

        # checking if the server stored their name
        if player_discord_id in player_discord_ids:
            try:
                player = await self.bot.api.get_player(player=player_discord_ids[player_discord_id])
                full_player = await player
                return full_player
            except NotFound:
                return -1
            except Private:
                return -2
            except Unavailable:
                return -3
            except HTTPException:
                return -7
        else:
            return None

    async def get_player_account(self, player_name):
        """Returns a [Player] account or an error as an INT."""
        try:
            player_name = player_name.lower()
        except AttributeError:  # it's already been processed
            return player_name

        # This player is already in the dictionary and therefore we don't need to waste an api call to get the player id
        if player_name in self.bot.cached_player_ids:
            try:
                player = await self.bot.api.get_player(player=self.bot.cached_player_ids[player_name])
                full_player = await player

                # Don't store a massive amount in the cache to try to Help Memory
                if len(self.bot.cached_player_ids) > 1500:
                    print("Cleared the internal Cache !!!!!!!!!!!!!!!!!!!")
                    self.bot.cached_player_ids.clear()

                return full_player
            except NotFound:
                return -1
            except Private:
                return -2
            except Unavailable:
                return -3
            except HTTPException:
                return -7
        else:
            if " " not in player_name:
                try:
                    player = await self.bot.api.get_player(player=player_name)
                except NotFound:
                    return -1
                except Private:
                    return -2
                except Unavailable:
                    return -3
                except HTTPException:
                    return -7

            else:  # Console name
                player_name, platform = player_name.rsplit(' ', 1)
                if player_name in self.bot.cached_player_ids:
                    return self.bot.cached_player_ids[player_name]
                try:
                    platform = ARezPlatform(platform)
                    if platform:
                        players = await self.bot.api.search_players(player_name=player_name, platform=platform)
                        if len(players) > 1:
                            return -5
                        # The one player name
                        player = players[0]

                        # check private players searched for
                        if player.private:
                            return -2
                    else:
                        return -4

                except NotFound:
                    return -1

            new_id = int(player.id)
            self.bot.cached_player_ids[player_name] = new_id  # store the new id in the dictionary
            full_player = await player
            return full_player

    async def get_player_id(self, player_name):
        """
        Similar to the above [get_player_account] function except that this function always returns an INT
        Returns an int with an error or player_id
        """

        player_name = player_name.lower()

        # This player is already in the dictionary and therefore we don't need to waste an api call to get the player id
        if player_name in self.bot.cached_player_ids:
            return self.bot.cached_player_ids[player_name]
        else:
            if " " not in player_name:
                try:
                    player = await self.bot.api.get_player(player=player_name)
                except NotFound:
                    return -1
                except Private:
                    return -2
                except Unavailable:
                    return -3
                except HTTPException:
                    return -7

            else:  # Console name
                player_name, platform = player_name.rsplit(' ', 1)
                if player_name in self.bot.cached_player_ids:
                    return self.bot.cached_player_ids[player_name]
                try:
                    platform = ARezPlatform(platform)
                    if platform:
                        players = await self.bot.api.search_players(player_name=player_name, platform=platform)
                        if len(players) > 1:
                            return -5
                        # The one player name
                        player = players[0]

                        # check private players searched for
                        if player.private:
                            return -2
                    else:
                        return -4

                except NotFound:
                    return -1

            new_id = int(player.id)
            self.bot.cached_player_ids[player_name] = new_id  # store the new id in the dictionary
            return new_id

    async def get_cache_file(self, cache_name):
        cache_file_name = self.id_cache
        if cache_name == 'me2':
            cache_file_name = self.id_cache2
        elif cache_name == 'me3':
            cache_file_name = self.id_cache3

        return cache_file_name


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(CommandUtils(bot))
