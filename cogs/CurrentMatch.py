from discord.ext import commands
from discord import Embed, colour, File
from arez.player import Player
from arez import HTTPException
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import my_utils as helper
from my_utils import force_whitespace as fw


class CurrentCog(commands.Cog):
    """Holds the command for the current command. This power house uses a lot of API calls to get the
    stats of all players currently in a LIVE match."""

    def __init__(self, bot):
        self.bot = bot

    invalid_queues = ["Unknown", "Shooting Range", "Training Siege", "Training Onslaught",
                      "Training Team Deathmatch", "Test Maps"]

    # Gets details about a player in a current match using the Paladins API
    # Get stats for a player's current match.
    @commands.command(name='current', pass_context=True,
                      aliases=["Current", "partida", "Partida", "obecny", "Obecny"],
                      ignore_extra=False)
    @commands.cooldown(30, 30, commands.BucketType.user)
    async def current(self, ctx, p_name):
        lang = await self.bot.command_utils.check_language(ctx=ctx)

        async with ctx.channel.typing():
            current_player = await self.bot.command_utils.process_name(author_id=ctx.author.id, player_name=p_name)

            if not isinstance(current_player, Player):
                await ctx.send(embed=await self.bot.command_utils.process_error(error_number=current_player,
                                                                                player_name=p_name, lang=lang))
                return None

            # process the player status
            current_data = await current_player.get_status()
            player_status = current_data.status.name
            # print(player_status)
            if player_status != "In Match":
                status_embed = await self.process_player_status(player_status=player_status,
                                                                player_name=current_player.name)
                await ctx.send(embed=status_embed)
                return None

            # process the player queue
            if current_data.queue:
                p_queue = current_data.queue.name
                if p_queue in self.invalid_queues or 'Custom' in p_queue:
                    queue_embed = await self.process_player_queue(player_queue=p_queue, player_name=current_player.name)
                    await ctx.send(embed=queue_embed)
                    return None
            else:
                p_queue = "???, player isn't in a match."

            try:
                lm = await current_data.get_live_match()
            except HTTPException:
                await ctx.send("API timeout, please try again :(")
                return None

            # This should never get called now but will leave in just in case (1/10/2021)
            if lm is None:
                await ctx.send("Issue finding {}'s match. They are likely in an LTM.".format(current_player.name))
                # await helper.log_live_error(bot=self.bot, messages=[current_player.name, player_status, p_queue])
                return None

            player_ids, player_ids2 = [lp.player.id for lp in lm.team1], [lp.player.id for lp in lm.team2]
            team1_champs, team2_champs = [lp.champion.name for lp in lm.team1], [lp.champion.name for lp in lm.team2]

            await lm.expand_players()   # expands players to be able to get the necessary data

            # Testing to see if we can still process the data for this person
            if current_data.queue is None:
                print("[Queue is None]")
                print(current_data.queue)
                print("^^^^^^^^^^^^^^^^^")

            team1_ranks, team2_ranks = [], []
            # get player ranks if in ranked match
            if current_data.queue.is_ranked():
                is_kbm = True if current_data.queue.value == 486 else False
                for p_id, r in zip(player_ids, lm.team1):
                    # print(current_data.queue.value, p_id, self.bot.cached_kbm_gm)
                    if p_id in self.bot.cached_kbm_gm:
                        team1_ranks.append('27')
                    else:
                        team1_ranks.append(str(r.rank.value))

                for p_id, r in zip(player_ids2, lm.team2):
                    # print(current_data.queue.value, p_id, self.bot.cached_kbm_gm)
                    if p_id in self.bot.cached_kbm_gm:
                        team2_ranks.append('27')
                    else:
                        team2_ranks.append(str(r.rank.value))

            buffer = await self.create_match_image(team1_champs, team2_champs, team1_ranks, team2_ranks)

            match_data = current_player.name + " is in a " + p_queue + " match."  # Match Type

            if current_data.queue.is_ranked():
                match_data += str('\n\n{:17} {:5} {:8} {:6}\n\n').format("Player name", "Lv.", "WR", "TP")

                data1 = await self.process_live_players_ranked(team_ids=player_ids, players=lm.team1, kbm=is_kbm)
                data2 = await self.process_live_players_ranked(team_ids=player_ids2, players=lm.team2, kbm=is_kbm)

                for pl in data1:
                    match_data += '{:17} {:5} {:8} {:6}\n'.format(pl[0], str(pl[1]), pl[2], str(pl[3]))

                match_data += "\n"

                for pl in data2:
                    match_data += '{:17} {:5} {:8} {:6}\n'.format(pl[0], str(pl[1]), pl[2], str(pl[3]))

            else:
                match_data += str('\n\n{:18}  {:7}  {:8}  {:6}\n\n').format("Player name", "Level", "Win Rate", "KDA")

                data1 = await self.process_live_players(team_ids=player_ids, players=lm.team1)
                data2 = await self.process_live_players(team_ids=player_ids2, players=lm.team2)

                team1_overall, team2_overall = [0, 0, 0, 0], [0, 0, 0, 0]  # num, level, win rate, kda
                match_data = await self.create_match_string_data(msg=match_data, data=data1, champs=team1_champs,
                                                                 team_overall=team1_overall)
                match_data += "\n"
                match_data = await self.create_match_string_data(msg=match_data, data=data2, champs=team2_champs,
                                                                 team_overall=team2_overall)

                # Overalls (Fun fact: this is spelled the same as the type of clothing.)
                team1_wr, team2_wr = 0, 0
                team1_level, team2_level = 0, 0
                team1_kda, team2_kda = 0, 0
                if team1_overall[0] != 0:
                    team1_wr = round(team1_overall[2] / team1_overall[0], 2)
                    team1_level = str(int(team1_overall[1] / team1_overall[0]))
                    team1_kda = str(round(team1_overall[3] / team1_overall[0], 2))
                if team2_overall[0] != 0:
                    team2_wr = round(team2_overall[2] / team2_overall[0], 2)
                    team2_level = str(int(team2_overall[1] / team2_overall[0]))
                    team2_kda = str(round(team2_overall[3] / team2_overall[0], 2))

                match_data += "\n\nAverage stats\n"
                ss1 = str('*{:18} Lv. {:3}  {:8}  {:6}\n')
                ss2 = str('*{:18} Lv. {:3}  {:8}  {:6}')

                # no need to call this if one team is 0
                if team1_wr != 0 and team2_wr != 0:
                    if abs(team1_wr - team2_wr) >= 5.0:
                        if team1_wr > team2_wr:
                            ss1 = ss1.replace("*", "+")
                            ss2 = ss2.replace("*", "-")
                        else:
                            ss1 = ss1.replace("*", "-")
                            ss2 = ss2.replace("*", "+")

                if team1_overall[0] != 0:
                    ss1 = ss1.format("Team1", team1_level, str(team1_wr), team1_kda)
                    match_data += ss1
                if team2_overall[0] != 0:
                    ss2 = ss2.format("Team2", team2_level, str(team2_wr), team2_kda)
                    match_data += ss2

            file = File(filename="Team.png", fp=buffer)
            await ctx.send("```diff\n" + match_data + "```", file=file)

    @staticmethod
    async def process_live_players(team_ids, players):
        data = []
        for p_id, p in zip(team_ids, players):
            if p_id == 0:
                data.append(["Private Account", "???", "???", "???"])
            else:
                player = p.player
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

                data.append([player.name, player.level, wr, kda])
        return data

    @staticmethod
    async def process_live_players_ranked(team_ids, players, kbm):
        data = []
        for p_id, p in zip(team_ids, players):
            if p_id == 0:
                data.append(["Private Account", "???", "???", "???"])
            else:
                player = p.player

                wr = player.ranked_keyboard.winrate if kbm else player.ranked_controller.winrate
                # print(wr) TODO fix the nan thing
                wr = '{0:.2f}'.format(wr * 100)
                tp = player.ranked_keyboard.points if kbm else player.ranked_controller.points

                data.append([player.name, player.level, wr, tp])
        return data

    @staticmethod
    async def process_player_status(player_status, player_name):
        if player_status == "Offline":
            embed_text = "\N{CROSS MARK} {} is Offline. \N{CROSS MARK}".format(player_name)
        elif player_status == "In Lobby":
            embed_text = "\N{PERSONAL COMPUTER} {} is in the lobby. \N{PERSONAL COMPUTER}".format(player_name)
        elif player_status == "Online":
            embed_text = "\N{PERSONAL COMPUTER} {} is online. \N{PERSONAL COMPUTER}".format(player_name)
        elif player_status == "Character Selection":
            embed_text = "\N{CROSSED SWORDS} {} is in champion selection. \N{CROSSED SWORDS}".format(player_name)
        else:
            embed_text = "\N{BLACK QUESTION MARK ORNAMENT} {} has an unknown status. \N{BLACK QUESTION MARK ORNAMENT}" \
                .format(player_name)
        status_embed = Embed(
            title=embed_text,
            colour=colour.Color.dark_teal()
        )
        return status_embed

    @staticmethod
    async def process_player_queue(player_queue, player_name):
        if player_queue == "Shooting Range":
            embed_text = "\N{WARNING SIGN} {} is in the `Shooting Range`. \N{WARNING SIGN}".format(player_name)
        elif player_queue == "Training Siege":
            embed_text = "\N{WARNING SIGN} {} is in a `Training Siege` match. \N{WARNING SIGN}".format(player_name)
        elif player_queue == "Training Onslaught":
            embed_text = "\N{WARNING SIGN} {} is in a `Training Onslaught` match. \N{WARNING SIGN}".format(player_name)
        elif player_queue == "Training Team Deathmatch":
            embed_text = "\N{WARNING SIGN} {} is in a `Training TDM`. \N{WARNING SIGN}".format(player_name)
        elif player_queue == "Test Maps":
            embed_text = "\N{WARNING SIGN} {} is in a `Test Map` match. \N{WARNING SIGN}".format(player_name)
        elif 'Custom' in player_queue:
            embed_text = "\N{WARNING SIGN} {} is in a `Custom` match on `{}`. \N{WARNING SIGN}"\
                .format(player_name, player_queue.replace('Custom', '').strip())
        else:
            embed_text = "\N{BLACK QUESTION MARK ORNAMENT} {} is in an unknown match. \N{BLACK QUESTION MARK ORNAMENT}"\
                .format(player_name)

        queue_embed = Embed(
            title=embed_text,
            colour=colour.Color.dark_teal()
        )
        return queue_embed

    @staticmethod
    async def create_match_string_data(msg, data, champs, team_overall):
        """Strings are immutable and therefore must be returned. Lists are mutable >_>"""
        for pl, champ in zip(data, champs):
            ss = '*{:18} Lv. {:3}  {:8}  {:6}\n'.format(pl[0], str(pl[1]), pl[2], pl[3])

            """This Block of code adds color based on Win Rate"""
            if "???" in pl[2]:
                pass
            elif (float(pl[2].replace(" %", ""))) > 55.00:
                ss = ss.replace("*", "+")
            elif (float(pl[2].replace(" %", ""))) < 49.00:
                ss = ss.replace("*", "-")
            """^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"""
            msg += ss

            # For teams totals
            if pl[1] != "???" and float(pl[1]) > 50:
                team_overall[0] += 1             # num
                team_overall[1] += int(pl[1])    # level
                team_overall[2] += float(pl[2])  # win rate
                team_overall[3] += float(pl[3])  # kda
        return msg

    # Creates a match image based on the two teams champions
    async def create_match_image(self, team1, team2, ranks1, ranks2):
        buffer1 = await self.create_team_image(team1, ranks1)
        buffer2 = await self.create_team_image(team2, ranks2)
        middle = await self.draw_match_vs()

        offset = 128

        image_size = 512
        match_image = Image.new('RGB', (image_size * len(team1), image_size * 2 + offset))

        # box – The crop rectangle, as a (left, upper, right, lower)- tuple.

        # Row 1
        match_image.paste(Image.open(buffer1), (0, 0, (image_size * len(team1)), image_size))

        # Middle row
        match_image.paste(Image.open(middle), (0, image_size, (image_size * len(team1)), image_size + offset))

        # Row 2
        match_image.paste(Image.open(buffer2),
                          (0, image_size + offset, (image_size * len(team1)), image_size * 2 + offset))

        #                                                                                   Base speed is: 10 seconds
        # match_image = match_image.resize((int(1280), int(576)), Image.Resampling.LANCZOS)          # 5 seconds
        match_image = match_image.resize((1280, 576))  # 5 seconds (looks good)
        # match_image = match_image.resize((int(2560/3), int(1152/3)), Image.Resampling.LANCZOS)     # 2-3 seconds
        # match_image = match_image.resize((int(2560 / 4), int(1152 / 4)), Image.Resampling.LANCZOS) # 2-3 seconds
        # match_image.show()

        # Creates a buffer to store the image in
        final_buffer = BytesIO()

        # Store the pillow image we just created into the buffer with the PNG format
        match_image.save(final_buffer, "png")

        # seek back to the start of the buffer stream
        final_buffer.seek(0)

        return final_buffer

    # Creates an team image by using champion Icons
    @staticmethod
    async def create_team_image(champ_list, ranks):
        champion_images = []

        while len(champ_list) != 5:
            champ_list.append("?")

        for champ in champ_list:
            if champ != "?" and champ is not None:
                try:
                    champion_images.append(
                        Image.open("icons/champ_icons/{}.png".format(await helper.convert_champion_name_image(champ))))
                except FileNotFoundError:
                    image_size = 512
                    base = Image.new('RGB', (image_size, image_size), "black")
                    icon = Image.open("icons/miscellaneous/unknown.png")
                    icon = icon.resize((512, 352), Image.Resampling.LANCZOS)
                    base.paste(icon, (0, 80))
                    champion_images.append(base)
            else:
                image_size = 512
                base = Image.new('RGB', (image_size, image_size), "black")
                icon = Image.open("icons/miscellaneous/unknown.png")
                icon = icon.resize((512, 352), Image.Resampling.LANCZOS)
                base.paste(icon, (0, 160))

                # put text on image
                base_draw = ImageDraw.Draw(base)
                base_draw.text((140, 10), "Bot", font=ImageFont.truetype("arial", 140))
                champion_images.append(base)

        # Original Image size # print(width, height)
        image_size = 512
        scale = 1.5
        # champion_images.append(img.resize((image_size, image_size)))

        team_image = Image.new('RGB', (image_size * len(champion_images), image_size))
        for i, champ in enumerate(champion_images):
            team_image.paste(champ, (image_size * i, 0, image_size * (i + 1), image_size))

            # Only try to use ranked icons if its a ranked match
            if ranks:
                if i < len(ranks):  # make sure we don't go out of bounds
                    rank = Image.open("icons/ranks/" + ranks[i] + ".png")  # this works
                    width, height = rank.size
                    rank = rank.resize((int(width * scale), int(height * scale)))
                    team_image.paste(rank, (0 + (image_size * i), 0), rank)  # Upper Left

        # Testing
        # team_image.show()

        # Creates a buffer to store the image in
        final_buffer = BytesIO()

        # Store the pillow image we just created into the buffer with the PNG format
        team_image.save(final_buffer, "png")

        # seek back to the start of the buffer stream
        final_buffer.seek(0)

        return final_buffer

    # Draws a question in place of missing information for images
    @staticmethod
    async def draw_match_vs():
        base = Image.new('RGB', (2560, 128), "black")

        # put text on image
        base_draw = ImageDraw.Draw(base)
        base_draw.text((1248, 32), "VS", font=ImageFont.truetype("arial", 64))

        # Creates a buffer to store the image in
        final_buffer = BytesIO()

        # Store the pillow image we just created into the buffer with the PNG format
        base.save(final_buffer, "png")

        # seek back to the start of the buffer stream
        final_buffer.seek(0)

        return final_buffer


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(CurrentCog(bot))
