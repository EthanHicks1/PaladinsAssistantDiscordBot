from discord import Embed, colour
from discord.ext import commands
from fuzzywuzzy import process
from arez.player import Player
import my_utils as helper
import argparse
import shlex


# Class handles commands related a player's previous matches
class MatchHistoryCommands(commands.Cog, name="Match History Commands"):
    """Match History Commands"""

    def __init__(self, bot):
        self.bot = bot
        self.queues = ["TDM", "Ranked", "Onslaught", "KOTH", "Siege"]

        class SafeParser(argparse.ArgumentParser):
            def error(self, message):
                raise ValueError(message)

            def exit(self, status=0, message=None):
                pass

        self.my_parser = SafeParser()
        self.my_parser.add_argument('-c', '--champion', action='store', type=str, required=False)
        self.my_parser.add_argument('-q', '--queue', action='store', type=str, required=False)
        self.my_parser.add_argument('-r', '--role', action='store', type=str, required=False)

    @classmethod
    # Used to change text prefix to change it's color
    async def color_win_rates(cls, text, win_rate):
        if float(win_rate) > 60.0:
            return "+" + text
        elif float(win_rate) < 50.0 and float(win_rate) != 0.0:
            return "-" + text
        else:
            return "*" + text

    @classmethod
    # Converts the match name so that its small enough to fit on one line
    async def convert_match_type(cls, match_type):
        # https://arez.readthedocs.io/en/latest/enums.html#arez.Queue
        # Should return up to 9 character limit for formatting
        if match_type.is_ranked():
            return 'Ranked'
        elif match_type.is_onslaught():
            return 'Onslaught'
        elif match_type.is_tdm():
            return 'TDM'
        elif match_type.is_koth():  # IDK if this will ever be hit
            return 'KOTH'
        elif match_type.is_training():
            return 'Bot Match'
        elif match_type.is_custom():
            return 'Custom'
        elif 'Payload' in match_type.name:
            return 'Payload'
        else:
            # Default "Casuals" and all other modes to type siege
            # print(match_type.name)
            return 'Siege'

    async def process_queue_type(self, match_name):
        matched_queue, match_percent = process.extractOne(match_name, self.queues)
        if match_percent >= 75:
            return matched_queue
        else:
            return None

    @commands.command(name='history', pass_context=True, ignore_extra=False,
                      aliases=["History", "historia", "Historia"])
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def history(self, ctx, *args):
        lang = await self.bot.command_utils.check_language(ctx=ctx)

        try:
            player_name = args[0]
        except IndexError:
            no = Embed(
                title="\N{WARNING SIGN} {} \N{WARNING SIGN}".format("Missing player name parameter."),
                colour=colour.Color.red(),
            )
            await ctx.send(embed=no)
            return None

        current_player = await self.bot.command_utils.process_name(author_id=ctx.author.id, player_name=player_name)

        if not isinstance(current_player, Player):
            await ctx.send(embed=await self.bot.command_utils.process_error(error_number=current_player,
                                                                            player_name=player_name,
                                                                            lang=lang))
            return None

        async with ctx.channel.typing():
            try:
                args = self.my_parser.parse_args(shlex.split(' '.join(args[1:])))
            except ValueError:
                no = Embed(
                    title="\N{WARNING SIGN} {} \N{WARNING SIGN}".format("Invalid parameters provided."),
                    description="Make sure you provide a parameter after a variable and that it's a valid parameter. "
                                "Please see `>>help history` for formatting and examples of this command.",
                    colour=colour.Color.red(),
                )
                await ctx.send(embed=no)
                return None

            # process champion name
            champ_name = args.champion
            if champ_name is None:
                champ_name = ""
            else:
                champ_name = await helper.process_champion_name(champ_name)
                if not champ_name:
                    raise ValueError("InvalidChampName", args.champion)

            # process queue name
            if args.queue is None:
                queue_type = ""
            else:
                queue_type = await self.process_queue_type(args.queue)
                if queue_type is None:
                    valid_queue_names_embed = Embed(
                        title="\N{WARNING SIGN} {} \N{WARNING SIGN}".format("Invalid queue type."),
                        description="Valid queue names are list below: \n"
                                    "``` {} ```".format(', '.join(self.queues)),
                        colour=colour.Color.red(),
                    )
                    await ctx.send(embed=valid_queue_names_embed)
                    return None

            # Can raise private account error but should not need to catch that
            paladins_matches = await current_player.get_match_history()

            # Check to see if this player does have match history
            if not paladins_matches:
                embed = Embed(
                    title="\N{WARNING SIGN} No Match History \N{WARNING SIGN}",
                    description=f'**`{player_name}`** has not played any matches in the last 30 days.',
                    colour=colour.Color.orange()
                )
                await ctx.send(embed=embed)
                return None

            count = 0
            total_matches = 0
            match_data = ""
            match_data2 = ""
            # Damage, Flank, Tank, Support => (win, lose)
            total_wins = [0, 0, 0, 0, 0, 0, 0, 0]
            # Damage, Flank, Tank, Support => (kda, total_matches per class)
            total_kda = [0, 0, 0, 0, 0, 0, 0, 0]
            global_kda = 0.0

            for partial_match in paladins_matches:
                # match = await partial_match # doesn't seem needed
                match_champ_name = partial_match.champion.name

                # empty string means to get everything or only get matches with a certain champ
                if not champ_name or champ_name == match_champ_name.replace("'", " "):  # Mal'Damba
                    ss = str('+{:10}{:3}:00 {:9} {:9} {:5} ({}/{}/{})\n')
                    kills = partial_match.kills
                    deaths = partial_match.deaths
                    assists = partial_match.assists
                    kda = await helper.calc_kda(kills, deaths, assists)
                    # print(partial_match.queue.name)
                    match_name = await self.convert_match_type(partial_match.queue)

                    # if a queue_type is not mentioned or only grab those of a specific type
                    if not queue_type or queue_type == match_name:
                        # we don't want to count event or bot matches when calculating stats
                        if match_name != "Bot Match" and match_name != "Test Maps":
                            # Cause her name is too long...
                            display_name = 'Betty' if 'Betty' in match_champ_name else match_champ_name
                            # Correction for processing name
                            if 'Mal' in match_champ_name:
                                match_champ_name = 'Mal Damba'
                            ss = ss.format(display_name, partial_match.duration.minutes,
                                           match_name, partial_match.id, kda, kills, deaths, assists)

                            global_kda += float(kda)
                            total_matches += 1
                            class_index = self.bot.champs.get_champ_class(match_champ_name)
                            if class_index != -1:
                                total_kda[class_index * 2] += float(kda)
                                total_kda[class_index * 2 + 1] += 1
                                if partial_match.winner:
                                    total_wins[class_index * 2] += 1  # Wins
                                else:
                                    total_wins[class_index * 2 + 1] += 1  # Losses
                            else:
                                print("Unclassified champion: " + str(match_champ_name))

                            # Used for coloring
                            if not partial_match.winner:
                                ss = ss.replace("+", "-")

                            if count >= 30:
                                match_data2 += ss
                            else:
                                match_data += ss

                            # Making sure we display the correct number of matches
                            count += 1

            if not match_data and champ_name:
                await ctx.send("Could not find any matches with the champion: `" + champ_name +
                               "` in the last 50 matches")
                return None

            # Base string to hold kda and win rate for all classes
            ss = "Class      KDA:  Win Rate:\n\n" \
                 "Total:   {:5}  {:6}% ({}-{})\n" \
                 "Damages: {:5}  {:6}% ({}-{})\n" \
                 "Flanks:  {:5}  {:6}% ({}-{})\n" \
                 "Tanks:   {:5}  {:6}% ({}-{})\n" \
                 "Healers: {:5}  {:6}% ({}-{})\n\n"

            # Calculating win rates
            d_t = total_wins[0] + total_wins[1]  # Damage total matches
            f_t = total_wins[2] + total_wins[3]  # Flank total matches
            t_t = total_wins[4] + total_wins[5]  # Tank total matches
            s_t = total_wins[6] + total_wins[7]  # Healer total matches
            d_wr = await helper.calc_win_rate(total_wins[0], d_t)
            f_wr = await helper.calc_win_rate(total_wins[2], f_t)
            t_wr = await helper.calc_win_rate(total_wins[4], t_t)
            s_wr = await helper.calc_win_rate(total_wins[6], s_t)

            # Total wins/loses
            if total_matches == 0:  # prevent division by 0
                total_matches = 1
            global_kda = round(global_kda / total_matches, 2)
            tot_wins = total_wins[0] + total_wins[2] + total_wins[4] + total_wins[6]
            tot_loses = total_wins[1] + total_wins[3] + total_wins[5] + total_wins[7]
            total_wr = await helper.calc_win_rate(tot_wins, d_t + f_t + t_t + s_t)

            # Coloring based off of class/total win rates
            ss = ss.replace("Total", await self.color_win_rates("Total", total_wr)) \
                .replace("Damages", await self.color_win_rates("Damages", d_wr)) \
                .replace("Flanks", await self.color_win_rates("Flanks", f_wr)) \
                .replace("Tanks", await self.color_win_rates("Tanks", t_wr)) \
                .replace("Healers", await self.color_win_rates("Healers", s_wr))

            # KDA calc
            d_kda, f_kda, t_kda, s_kda, = 0.0, 0.0, 0.0, 0.0
            if total_kda[0] != 0:
                d_kda = round(total_kda[0] / total_kda[1], 2)
            if total_kda[2] != 0:
                f_kda = round(total_kda[2] / total_kda[3], 2)
            if total_kda[4] != 0:
                t_kda = round(total_kda[4] / total_kda[5], 2)
            if total_kda[6] != 0:
                s_kda = round(total_kda[6] / total_kda[7], 2)

            # Filling the the string with all the data
            ss = ss.format(global_kda, total_wr, tot_wins, tot_loses, d_kda, d_wr, total_wins[0], total_wins[1], f_kda,
                           f_wr, total_wins[2], total_wins[3], t_kda, t_wr, total_wins[4], total_wins[5], s_kda, s_wr,
                           total_wins[6], total_wins[7])

            title = str('{}\'s last {} matches:\n\n').format(str(player_name), count)
            title += str('{:11} {:5} {:9} {:10} {:5} {}\n').format("Champion", "Time", "Mode", "Match ID",
                                                                   "KDA", "Detailed")
            title += match_data
        await ctx.send("```diff\n" + title + "```")
        match_data2 += "\n\n" + ss
        await ctx.send("```diff\n" + match_data2 + "```")


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(MatchHistoryCommands(bot))
