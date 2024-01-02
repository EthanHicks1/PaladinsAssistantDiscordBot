from discord.ext import commands
from discord import Embed, colour, NotFound
from arez.player import Player
from arez import Language
import asyncio
import os.path
import os
import time
import re

from colorama import Fore
import my_utils as helper

# Built in discord UI
from discord import SelectOption, Interaction, ButtonStyle
from discord.errors import HTTPException
from discord.ui import Select, Button

from MyCustomDiscordView import MyGenericView


# All functions in this class use Pyrez wrapper to access Paladins API
class PaladinsAPICog(commands.Cog, name="Paladins API Commands"):
    """PaladinsAPICog"""

    def __init__(self, bot):
        self.bot = bot

    # Gets the overall player stats of a player
    async def get_player_stats_api(self, author_id, player_name, lang):
        start = time.time()
        cur_p = await self.bot.command_utils.process_name(author_id=author_id, player_name=player_name)

        if not isinstance(cur_p, Player):
            return await self.bot.command_utils.process_error(error_number=cur_p, player_name=player_name, lang=lang)

        if cur_p.title == '':
            embed = Embed(
                title="{} \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b "
                      "\u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b "
                      "\u200b \u200b \u200b \u200b \u200b \u200b ".format(cur_p.name),
                colour=colour.Color.dark_teal(),
            )
        else:
            # Clean title of Color HTML Tags
            clean = re.compile('<.*?>')
            cur_p.title = re.sub(clean, '', cur_p.title)

            embed = Embed(
                title="{} ({}) \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b "
                      "\u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b "
                      "\u200b \u200b \u200b \u200b \u200b \u200b ".format(cur_p.name, cur_p.title),
                colour=colour.Color.dark_teal(),
            )

        # Overall Info
        lang = 'en'
        ss = self.bot.cmd_lang_dict["stats_s1"][lang]
        p1, p2 = ss.split("*")

        _d = await self.get_global_stats(cur_p)
        # print(vars(info))
        # level = await helper.convert_level(cur_p.level, cur_p.total_experience)
        p2 = p2.format(cur_p.name, cur_p.calculated_level, _d[0], _d[1], _d[2], _d[3], cur_p.casual.leaves)
        embed.add_field(name="**__{}__**".format(p1), value="```{}```".format(p2), inline=False)

        # Ranked Info
        s2 = self.bot.cmd_lang_dict["stats_s2"][lang]

        # Get ranked stats ---------------------------------------------------------------------------------------------
        p1, p2 = s2.split("*")

        p2_copy = p2

        if cur_p.ranked_keyboard.matches_played == 0 and cur_p.ranked_controller.matches_played == 0:
            pass    # They haven't played ranked at all this split
        else:
            # Grab Season number
            if cur_p.ranked_keyboard.matches_played > 0:
                p1 = p1.format(cur_p.ranked_keyboard.season - 1)
            else:
                p1 = p1.format(cur_p.ranked_controller.season - 1)

            # Add in KBM stats
            if cur_p.ranked_keyboard.matches_played > 0:
                wr = await helper.calc_win_rate(cur_p.ranked_keyboard.wins, cur_p.ranked_keyboard.matches_played)

                rank_name = cur_p.ranked_keyboard.rank.name  # alt_name
                rank_pos = cur_p.ranked_keyboard.position
                tp = cur_p.ranked_keyboard.points

                rank_name = await helper.convert_rank(rank_name, rank_pos, tp)
                p2 = p2.format(rank_name, tp, rank_pos, wr, cur_p.ranked_keyboard.wins, cur_p.ranked_keyboard.losses,
                               cur_p.ranked_keyboard.leaves)

            # Add in Controller stats
            if cur_p.ranked_controller.matches_played > 0:
                wr = await helper.calc_win_rate(cur_p.ranked_controller.wins, cur_p.ranked_controller.matches_played)

                rank_name = cur_p.ranked_controller.rank.name
                rank_pos = cur_p.ranked_controller.position
                tp = cur_p.ranked_controller.points

                rank_name = await helper.convert_rank(rank_name, rank_pos, tp)

                # Add in the correct ranks
                if cur_p.ranked_keyboard.matches_played > 0:
                    p2 += '\n\n' + p2_copy.format(rank_name, tp, rank_pos, wr, cur_p.ranked_controller.wins,
                                                  cur_p.ranked_controller.losses, cur_p.ranked_controller.leaves)
                else:
                    p2 = p2_copy.format(rank_name, tp, rank_pos, wr, cur_p.ranked_controller.wins,
                                        cur_p.ranked_controller.losses, cur_p.ranked_controller.leaves)

            embed.add_field(name="**__{}__**".format(p1), value="```{}```".format(p2), inline=False)

        # Extra info ---------------------------------------------------------------------------------------------------
        s3 = self.bot.cmd_lang_dict["stats_s3"][lang]
        try:
            created = str(cur_p.created_at).split()[0]
        except IndexError:
            created = "Unknown"
        try:
            last = str(cur_p.last_login).split()[0]
        except IndexError:
            last = "Unknown"

        p1, p2 = s3.split("*")
        p2 = p2.format(created, last, cur_p.platform, cur_p.champion_count, cur_p.total_achievements)
        embed.add_field(name="**__{}__**".format(p1), value="```{}```".format(p2), inline=False)

        # get the extension if it exists
        ext = self.bot.champ_aliases.get(str(cur_p.avatar_id))

        # create the avatar_name (name.extension)
        if ext is None:
            avatar_name = "0.png"   # couldn't find the avatar
        else:
            avatar_name = str(cur_p.avatar_id) + "." + ext

        embed.set_thumbnail(url="https://raw.githubusercontent.com/EthanHicks1/PaladinsArtAssets/master/"
                                "avatars/{}".format(avatar_name))

        # Add in footer icon
        end = time.time()
        # print(info)
        embed.set_footer(text="Fetched data in {:.2f} seconds. Id: {}".format(end - start, cur_p.id),
                         icon_url="https://raw.githubusercontent.com/EthanHicks1/PaladinsArtAssets/master/"
                                  "avatars/0.png")
        return embed

    @staticmethod
    async def get_global_stats(player):
        champ_list = await player.get_champion_stats()

        t_wins = t_loses = t_kda = count = 0

        for champ in champ_list:
            wins = champ.wins
            losses = champ.losses
            kda = await helper.calc_kda(champ.kills, champ.deaths, champ.assists)
            t_wins += wins
            t_loses += losses
            t_kda += float(kda) * (wins + losses)  # These two lines allow the kda to be weighted
            count += (wins + losses)  # aka the more a champ is played the more it affects global kda

        if count == 0:
            kda = "???"
        else:
            kda = str('{0:.2f}').format(t_kda / count)
        wr = await helper.calc_win_rate(t_wins, count)

        return [wr, t_wins, t_loses, kda]

    # Gets stats for a specific champion
    async def get_champ_stats_api(self, author_id, player_name, champ_name, easter_egg_name, lang):
        start = time.time()
        current_player = await self.bot.command_utils.process_name(author_id=author_id, player_name=player_name)

        if not isinstance(current_player, Player):
            return await self.bot.command_utils.process_error(error_number=current_player,
                                                              player_name=player_name, lang=lang)

        try:
            champ_list = await current_player.get_champion_stats()
        except BaseException:
            match_data = self.bot.cmd_lang_dict["general_error2"][lang].format(player_name)
            embed = Embed(
                description=match_data,
                colour=colour.Color.dark_teal()
            )
            return embed

        if "Mal" in champ_name:
            champ_name = "Mal'Damba"

        ss = ""
        t_wins = t_loses = t_kda = count = 0

        for champ in champ_list:
            wins = champ.wins
            losses = champ.losses
            kda = await helper.calc_kda(champ.kills, champ.deaths, champ.assists)
            t_wins += wins
            t_loses += losses
            t_kda += float(kda) * (wins + losses)  # These two lines allow the kda to be weighted
            count += (wins + losses)  # aka the more a champ is played the more it affects global kda

            # champ we want to get the stats on
            if champ.champion.name == champ_name:
                win_rate = await helper.calc_win_rate(wins, wins + losses)
                level = champ.level

                try:
                    last_played = champ.last_played
                except None:  # Bought the champ but never played them
                    last_played = "???"
                    await helper.log_live_error(bot=self.bot, messages=['LP: ', current_player.name, current_player.id])

                ss = self.bot.cmd_lang_dict["stats_champ"][lang].replace("*", " ")

                ss = ss.format(champ.champion.name, level, kda, champ.kills, champ.deaths, champ.assists,
                               win_rate, wins, losses, str(last_played).split()[0])  # str(stat.lastPlayed).split()[0]

        # They have not played this champion yet
        if ss == "":
            ss = "No data for champion: " + champ_name + "\n"
            embed = Embed(
                description=ss,
                colour=colour.Color.orange()
            )
            return embed

        # Global win rate and kda
        global_ss = str("\n\nGlobal KDA: {}\nGlobal Win Rate: {}% ({}-{})")
        win_rate = await helper.calc_win_rate(t_wins, t_wins + t_loses)
        t_kda = str('{0:.2f}').format(t_kda / count)
        global_ss = global_ss.format(t_kda, win_rate, t_wins, t_loses)
        ss += global_ss

        # Create an embed
        embed = Embed(
            title="{}'s stats:".format(current_player.name),
            description="```{}```".format(ss),
            colour=colour.Color.dark_teal()
        )

        # Add in icon image
        if easter_egg_name:
            champ_name = easter_egg_name
        # print((await helper.get_champ_image(champ_name)).replace('.png', '.jpg'))
        embed.set_thumbnail(url=await helper.get_champ_image(champ_name))
        end = time.time()
        embed.set_footer(text="Fetched data in {0:.2f} seconds.".format(end - start),
                         icon_url="https://raw.githubusercontent.com/EthanHicks1/PaladinsArtAssets/master/"
                                  "avatars/0.png")
        return embed

    class TopSelect(Select):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        async def callback(self, interaction: Interaction):
            self.view.current_selection = int(self.values[0])

            if self.view.previous_selection != self.view.current_selection:
                print(Fore.GREEN + "[DEBUG] user selected a valid option:", self.view.current_selection,
                      self.view.previous_selection)
                # User has selected an option for the first time so enable the buttons
                if self.view.previous_selection == -1:
                    for child in self.view.children:
                        if isinstance(child, Button):
                            child.disabled = False
                self.view.previous_selection = self.view.current_selection

                await self.view.send_msgs(interaction=interaction)
            else:
                print(Fore.RED + "[DEBUG] user selected the same option:",  self.view.current_selection,
                      self.view.previous_selection)
                # "Do nothing"... the user select the same option again... smh
                try:
                    await interaction.response.edit_message(view=self)
                except HTTPException:
                    pass

    class TopButtons(Button):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        async def callback(self, interaction: Interaction):
            if self.custom_id == 'Class':
                self.view.by_class = not self.view.by_class
                self.view.previous_selection = -2
            elif self.custom_id == 'Order':
                self.view.list_reversed = not self.view.list_reversed
                self.view.previous_selection = -2

            await self.view.send_msgs(interaction=interaction)

    class FancyView(MyGenericView):
        def __init__(self, *args, **kwargs):
            self.player_champion_data = kwargs.pop('player_champion_data')
            self.ctx = kwargs.pop('ctx')
            self.bot = kwargs.pop('bot')
            super().__init__(*args, **kwargs)

        by_class = False
        list_reversed = True
        previous_selection = -1
        previous_msgs = []
        current_selection = -1

        async def send_msgs(self, interaction: Interaction):
            print(Fore.GREEN + "[CALL STACK] send_msgs")
            # Update our view
            try:
                await interaction.response.edit_message(view=self)
                # await interaction.response.defer()
            except HTTPException:
                pass

            # Clean up the previously sent messages
            for msg in self.previous_msgs:
                try:
                    await msg.delete()
                except NotFound:
                    print("[TOP Command] --> [NotFound]: ", msg, "was not found")
                except HTTPException:
                    print("[TOP Command] --> [HTTPException]")
            self.previous_msgs.clear()

            # Sort the data
            player_champion_data = sorted(self.player_champion_data, key=lambda x: x[self.current_selection],
                                          reverse=self.list_reversed)

            paladins_class_type = ["", "", "", ""]
            class_type_index = [0, 0, 0, 0]

            # non-mobile version (mobile version no longer exists [11/13/2021])
            for i, champ in enumerate(player_champion_data, start=0):
                # convert all elements to string to make formatting easier
                champ = [str(j) for j in champ]
                hours = int(int(champ[5]) / 60)
                minutes = int(champ[5]) % 60
                champ[5] = "{}h {}m".format(hours, minutes)

                # Separate how the message will look
                if self.by_class:
                    c_index = self.bot.champs.get_champ_class(champ[0])
                    class_type_index[c_index] += 1
                    if class_type_index[c_index] <= 9:
                        paladins_class_type[c_index] \
                            += "{}.  {:15}{:5} {:6} {:8} {:8} {:6}\n".format(class_type_index[c_index],
                                                                             *champ)
                    else:
                        paladins_class_type[c_index] \
                            += "{}. {:15}{:5} {:6} {:8} {:8} {:6}\n".format(class_type_index[c_index],
                                                                            *champ)
                else:
                    if i >= 9:
                        if i < 30:
                            paladins_class_type[0] += "{}. {:15}{:5} {:6} {:8} {:8} {:6}\n" \
                                .format(i + 1, *champ)
                        else:
                            paladins_class_type[1] += "{}. {:15}{:5} {:6} {:8} {:8} {:6}\n" \
                                .format(i + 1, *champ)
                    else:
                        paladins_class_type[0] += "{}.  {:15}{:5} {:6} {:8} {:8} {:6}\n".format(i + 1,
                                                                                                *champ)

            # Send new message(s) and add them to our list to delete later if needed
            if self.by_class:
                print(Fore.CYAN + "[CALL STACK] self.by_class send messages")
                message = "{:15}    {:5} {:6} {:8} {:8} {:6}\n{}\n" \
                    .format("Champion", "Lv.", "KDA", "WR", "Matches", "Time",
                            "------------------------------------------------------------------")
                self.previous_msgs.append(await self.ctx.send("```md\n" + message + "#   Damage\n" +
                                                              paladins_class_type[0] + "```"))
                self.previous_msgs.append(await self.ctx.send("```md\n" + message + "#   Flank\n" +
                                                              paladins_class_type[1] + "```"))
                self.previous_msgs.append(await self.ctx.send("```md\n" + message + "#   Tank\n" +
                                                              paladins_class_type[2] + "```"))
                self.previous_msgs.append(await self.ctx.send("```md\n" + message + "#   Support\n" +
                                                              paladins_class_type[3] + "```"))
            else:
                print(Fore.CYAN + "[CALL STACK] send messages")
                message = "{:15}    {:5} {:6} {:8} {:8} {:6}\n{}\n" \
                    .format("Champion", "Lv.", "KDA", "WR", "Matches", "Time",
                            "------------------------------------------------------------------")
                self.previous_msgs.append(await self.ctx.send("```md\n" + message + paladins_class_type[0] + "```"))
                if paladins_class_type[1] != "":
                    self.previous_msgs.append(await self.ctx.send("```md\n" + paladins_class_type[1] + "```"))

            """
            try:
                await interaction.followup.edit_message(view=self)
            except HTTPException:
                pass
            """

    # Returns the highest or lowest stats sorted by different categories (Level, KDA, WL, Matches, Time)
    @commands.command(name='top', pass_context=True, ignore_extra=False, aliases=["Top"])
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def top(self, ctx, player_name):
        # Command Vars
        comp_timeout = 90

        lang = await self.bot.command_utils.check_language(ctx=ctx)

        current_player = await self.bot.command_utils.process_name(author_id=ctx.author.id, player_name=player_name)

        if not isinstance(current_player, Player):
            return await self.bot.command_utils.process_error(error_number=current_player,
                                                              player_name=player_name, lang=lang)

        async with ctx.channel.typing():
            champ_list = await current_player.get_champion_stats()

            player_champion_data = []

            for champ in champ_list:
                kda = await helper.calc_kda(champ.kills, champ.deaths, champ.assists)
                wr = await helper.calc_win_rate(champ.wins, champ.wins + champ.losses)
                player_champion_data.append([champ.champion.name, champ.level, kda, wr, champ.wins + champ.losses,
                                             int(champ.playtime.total_minutes())])

            # Convert option
            # ordering = False if ctx.invoked_with in ["Bottom", "bottom"] else True

            # This player has not played enough matches to have any data returned. (aka only played again bots)
            # (12/28/2021) I don't think this is needed anymore but will leave it for safety
            if not player_champion_data:
                error_embed = Embed(
                    title="\N{WARNING SIGN} {} \N{WARNING SIGN}".format("Too low of a level!!!"),
                    description="Please note if you are below level 5 you have only "
                                "faced bots and therefor don't have any player data to return.",
                    colour=colour.Color.red(),
                )
                await ctx.send(embed=error_embed)
                return None

            # custom emoji's aren't allowed yet <:paladins:841883429372166184> and <a:loading:842177005825949717>
            top_list = [SelectOption(label="Level", value="1"),
                        SelectOption(label="KDA", value="2"),
                        SelectOption(label="Win Rate", value="3"),
                        SelectOption(label="Matches", value="4"),
                        SelectOption(label="Time", value="5")]

            view_ui = self.FancyView(timeout=comp_timeout, author=ctx.author,
                                     player_champion_data=player_champion_data, ctx=ctx, bot=self.bot)

            test_menu = self.TopSelect(options=top_list, placeholder="Select an option", custom_id="TopMenu")
            view_ui.add_item(test_menu)

            role_button = self.TopButtons(style=ButtonStyle.green, label="Separate By Role", custom_id="Class",
                                          disabled=True)
            order_button = self.TopButtons(style=ButtonStyle.blurple, label="Reverse Order", custom_id="Order",
                                           disabled=True)
            view_ui.add_item(role_button)
            view_ui.add_item(order_button)

            # Debug
            print(self.bot.latencies)

            # Send msg
            view_ui.message = await ctx.send(f'This message will self destruct in {comp_timeout} seconds.',
                                             view=view_ui)

    def process_top_request(self, previous_msgs, player_champion_data, idx, sort_by_class, reverse_order):
        pass

    # Returns simple stats based on the option they choose (champ_name, or me)
    @commands.command(name='stats', aliases=['Stats', 'statystyki', 'Statystyki', 'statistiques', 'Statistiques'],
                      pass_context=True, ignore_extra=False)
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def stats(self, ctx, player_name, option=None):
        lang = await self.bot.command_utils.check_language(ctx=ctx)

        # get basic player stats
        if option is None:
            # for lang in Language:
            player_embed = await self.get_player_stats_api(player_name=player_name, author_id=ctx.author.id, lang=lang)
            await ctx.send(embed=player_embed)
            # await asyncio.sleep(5)
        # get stats for a specific character
        else:
            original_name = option
            if original_name.lower() in ['gurk', 'tony']:
                egg = original_name.lower()
            else:
                egg = None
            champ_name = await helper.process_champion_name(option)
            if not champ_name:
                raise ValueError("InvalidChampName", original_name)

            champ_embed = await self.get_champ_stats_api(author_id=ctx.author.id, player_name=player_name,
                                                         champ_name=champ_name, easter_egg_name=egg, lang=lang)
            await ctx.send(embed=champ_embed)


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(PaladinsAPICog(bot))
