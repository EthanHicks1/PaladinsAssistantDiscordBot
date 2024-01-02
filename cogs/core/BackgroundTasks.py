from discord import Status, Activity, ActivityType
from datetime import datetime, timezone, timedelta
from my_utils import get_est_time, log_live_error
from discord.ext import tasks, commands
from discord import Embed, Color
from colorama import Fore
import requests
import asyncio
import random
import json


class BackgroundTasks(commands.Cog):
    """This cog class handles the background functions run in the bot."""

    def __init__(self, bot):
        self.bot = bot

        # Start the background tasks
        self.presence_changer.start()
        if self.bot.IS_LIVE_BOT:  # only start the logging on the main bot
            self.log_information.start()
            self.cache_gm_lb.start()
            self.error_logger_cleaner.start()

    def get_server_count(self):
        return "{:,} Servers".format(len(self.bot.guilds))

    @staticmethod
    def get_steam_player_count():
        paladins = 'https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?format=json&appid=444090'
        return "{:,} Steam Players".format(requests.get(paladins).json()['response']['player_count'])

    def pick_activity(self):
        secure_random = random.SystemRandom()
        activity_list = [["Version 3.0.0", ActivityType.playing],
                         ["Paladins", ActivityType.playing],
                         ["Features", ActivityType.playing],
                         [">>help", ActivityType.playing],
                         [">>help", ActivityType.playing],
                         [self.get_server_count(), ActivityType.watching],
                         [self.get_steam_player_count(), ActivityType.watching]]

        return secure_random.choice(activity_list)

    @tasks.loop(minutes=1440.0, reconnect=True)
    async def error_logger_cleaner(self):
        """ Loop to check for deleting old error log messages once a day. """
        print("Started searching for messages to delete.")
        server = self.bot.get_guild(self.bot.DEV_GUILD_ID)
        channel = server.get_channel(self.bot.DEV_USER_ERROR_CHANNEL_ID)

        deletion_data = datetime.today() - timedelta(days=14)
        old_error_messages = [message async for message in channel.history(limit=None, before=deletion_data)]

        for msg in old_error_messages:
            # Just in case to prevent message deletion hanging
            if msg.author == self.bot.user:
                await msg.delete()

    @error_logger_cleaner.before_loop
    async def pre_error_logger_cleaner(self):
        print(Fore.LIGHTBLUE_EX + "Starting Error Logger Cleaner BackGround Task...")
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=120, reconnect=True)
    async def cache_gm_lb(self):
        """Only run this command on the main bot which shouldn't restart a lot"""
        try:    # PC/Gamepad master/gm lb
            data = self.bot.paladinsAPI.getLeagueLeaderboard(queueId=486, tier=26, split=1)
            self.bot.cached_kbm_gm.clear()
            dp = {}

            for p in data[:100]:
                points = p['Points']
                p_id = int(p['player_id'])
                if points > 100 and p_id != 0:
                    self.bot.cached_kbm_gm[p_id] = points

                # Increment the rank until we find an open index
                cur_rank = p['Rank']
                while cur_rank in dp:
                    cur_rank += 1

                dp[cur_rank] = '{},{},{},{}'.format(p['Name'], p['Points'], p['Wins'], p['Losses'])

            with open(self.bot.gm_lb_pc_data, 'w+', encoding='utf-8') as FP:
                json.dump(dp, FP)

        except BaseException as e:
            await log_live_error(bot=self.bot, messages=[e])

        await asyncio.sleep(30)  # just to make sure the files are fully updated before editing them
        await self.update_gm_lb_in_guilds()

    async def update_gm_lb_in_guilds(self):
        with open(self.bot.gm_lb_pc_data, 'r') as FP:
            _data = json.load(FP)

            msg, msg2, msg3, msg4 = '', '', '', ''
            for r, p in _data.items():
                pd = p.split(',')
                if int(r) <= 25:
                    msg += '{:3} {:16} {:6} {}/{}\n'.format(r, pd[0], pd[1], pd[2], pd[3])
                elif int(r) <= 50:
                    msg2 += '{:3} {:16} {:6} {}/{}\n'.format(r, pd[0], pd[1], pd[2], pd[3])
                elif int(r) <= 75:
                    msg3 += '{:3} {:16} {:6} {}/{}\n'.format(r, pd[0], pd[1], pd[2], pd[3])
                else:
                    msg4 += '{:3} {:16} {:6} {}/{}\n'.format(r, pd[0], pd[1], pd[2], pd[3])

            pc_embed = Embed(
                title='Keyboard Grandmaster Leaderboard',
                description='Last Updated: {} UTC'.format(
                    datetime.now(timezone.utc).strftime("%Y-%m-%d `%H:%M:%S`")),
                colour=Color.dark_teal()
            )

            pc_embed.add_field(name='Top 25', value='```Fix\n' + msg + '```', inline=False)
            pc_embed.add_field(name='26 - 50', value='```\n' + msg2 + '```', inline=False)
            pc_embed.add_field(name='51 - 75', value='```\n' + msg3 + '```', inline=False)
            pc_embed.add_field(name='76 - 100', value='```\n' + msg4 + '```', inline=False)

        with open(self.bot.gm_lb_cache_pc) as json_f:
            gm_lb = json.load(json_f)

            pc_count = len(gm_lb)

            for pc_guild_id, data in gm_lb.items():
                channel_id, msg_id = data.split(':')
                gm_msg = await self.bot.command_utils.get_msg_from_server(server_id=pc_guild_id,
                                                                          channel_id=channel_id,
                                                                          msg_id=msg_id, is_pc=True)
                if gm_msg:
                    await gm_msg.edit(embed=pc_embed)   # edit with updated info

        print(Fore.LIGHTBLUE_EX + "Done updating LB messages for {} guilds.".format(pc_count))

    @cache_gm_lb.before_loop
    async def pre_cache_gm_lb(self):
        print(Fore.LIGHTBLUE_EX + "Starting Cache GM LB BackGround Task...")
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=5.0, reconnect=True)
    async def presence_changer(self):
        """ Loop to change the bot presence every 5 minutes"""
        activity = self.pick_activity()
        await self.bot.change_presence(status=Status.dnd, activity=Activity(name=activity[0], type=activity[1]))

    @presence_changer.before_loop
    async def pre_presence_changer(self):
        print(Fore.LIGHTBLUE_EX + "Starting Presence Changer BackGround Task...")
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=20.0, reconnect=True)
    async def log_information(self):
        """
        # Logs to a file [guild count, support server count, errors, commands used, api calls used, date]
        # (every 20 minutes to get daily stats)
        """
        with open(self.bot.bot_log_file, 'r') as r_log_file:
            date = await get_est_time()
            date = date.split(" ")[1]

            lines = r_log_file.read().splitlines()
            servers, n1, old_errors, num_cmd, old_api_calls, old_date = lines[-1].split(',')
            api_calls = self.bot.paladinsAPI.getDataUsed()
            api_calls = api_calls.totalRequestsToday

            ss_c = str(len(self.bot.get_guild(self.bot.SUPPORT_GUILD_ID).members))

            current_daily_commands = self.bot.daily_command_count

            # Updates tracked information for the current day or the next day
            if old_date.strip() == date:
                current_daily_commands += int(num_cmd)
                lines[-1] = "{}, {}, {}, {}, {}, {}\n"\
                    .format(len(self.bot.guilds), ss_c, int(self.bot.daily_error_count) + int(old_errors),
                            current_daily_commands, api_calls, date)
                with open(self.bot.bot_log_file, 'w') as w_log_file:
                    w_log_file.write("\n".join(lines))
            else:
                with open(self.bot.bot_log_file, '+a') as a_log_file:
                    a_log_file.write("{}, {}, {}, {}, {}, {}\n"
                                     .format(len(self.bot.guilds), ss_c, int(self.bot.daily_error_count),
                                             current_daily_commands, api_calls, date))

        self.bot.daily_command_count = 0
        self.bot.daily_error_count = 0
        print("Logged commands uses and server count: {}".format(await get_est_time()))
        print("How large is the external name cache getting: {}".format(len(self.bot.cached_player_ids)))

    @log_information.before_loop  # A decorator that registers a coroutine to be called before the loop starts running
    async def pre_log_information(self):
        print(Fore.LIGHTBLUE_EX + "Starting Logger BackGround Task...")
        await self.bot.wait_until_ready()

    @commands.is_owner()
    @commands.command()
    async def check_tasks(self, ctx):
        await ctx.send("```Presence Changer:\n"
                       "Failed:  {}\n"
                       "Running: {}\n\n"
                       "Information Logger:\n"
                       "Failed:  {}\n"
                       "Running: {}```"
                       .format(self.presence_changer.failed(), self.presence_changer.is_running(),
                               self.log_information.failed(), self.log_information.is_running()))

    @commands.is_owner()
    @commands.command()
    async def restart_tasks(self, ctx):
        self.presence_changer.restart()
        if self.bot.IS_LIVE_BOT:
            self.log_information.restart()
            await ctx.send("Restarted tasks.")

    @commands.is_owner()
    @commands.command()
    async def start_tasks(self, ctx):
        self.presence_changer.start()
        if self.bot.IS_LIVE_BOT:
            self.log_information.restart()
            await ctx.send("Started presence_changer task.")

    # Self closing function.
    @commands.Cog.listener()
    async def close(self):
        """|coro|
        Logs out of Discord and closes all connections.
        (Doing this rapidly during testing can cause it fail on itself sometimes it seems ¯\_(ツ)_/¯ )
        """
        # close task that changes the bots presence
        self.presence_changer.cancel()

        # Set the bot to idle while shutting down
        await self.bot.change_presence(status=Status.idle, activity=Activity(name="Bot Shutdown",
                                                                             type=ActivityType.playing))

        await asyncio.sleep(55)

        # shut down logging task if it's the main bot
        if self.bot.IS_LIVE_BOT:
            self.log_information.cancel()
            self.cache_gm_lb.cancel()
            self.error_logger_cleaner.cancel()

        # Set the bot to offline right before Discord closes everything
        await self.bot.change_presence(status=Status.offline)
        await asyncio.sleep(5)  # make sure the status is set before shutting down

        # Built in function to close Discord bot
        await self.bot.close()


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(BackgroundTasks(bot))
