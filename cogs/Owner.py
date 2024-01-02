from pyrez.exceptions import PlayerNotFound, PrivatePlayer
from discord.ext import commands
from psutil import Process
from os import getpid
import time


class OwnerCog(commands.Cog, name="Bot Owner Commands"):
    """Hold commands that only the bot owner can use"""

    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(name='sac')
    async def sync_app_commands(self, ctx):
        """
        Based on the docs and with how Discord has this set up. Syncing only needs to occur when
        a command is added, removed, or modified. Therefore it's not good practice to run the sync command in either
        the [on_ready_event] or [setup_hook] entry point functions since there's an API Discord Limit for syncing.

        I personally find this a tad strange because this means that if a bot crashes and doesn't restart for a while,
        users will still see the option to run an application command but it will of course fail since the bot is
        offline. Sure this is probably a minor edge case but still seems a tad strange to me.
        """
        # MY_GUILD = discord.Object(id=537345551520366609)
        # await self.bot.tree.sync(guild=MY_GUILD) # Sync to a specific guild

        await ctx.send("Started Syncing App Commands...")
        async with ctx.channel.typing():
            start_t = time.time()
            await self.bot.tree.sync()  # Sync commands globally
            end_t = time.time()
            await ctx.send(f'Done Syncing App Commands! Took {end_t - start_t:.1f} seconds... '
                           f'however it can take up to an hour for global commands to actually be updated.')

    @commands.is_owner()
    @commands.command(name='check_bot', aliases=["bot_check"])
    async def check_bot(self, ctx):
        with open(self.bot.bot_log_file, 'r') as r_log_file:
            lines = r_log_file.read().splitlines()
            servers, n1, old_errors, num_cmd, old_api_calls, old_date = lines[-1].split(',')

        bot_memory = f'{round(Process(getpid()).memory_info().rss/1024/1024, 2)} MB'

        ss = "1. [Server count:]({})\n" \
             "2. [Help Server Members:]({})\n" \
             "3. [Fatal Errors:]({})\n" \
             "4. [Commands Used:]({})\n" \
             "5. [API Calls Used:]({})\n" \
             "6. [Date:]({})\n" \
             "7. [Memory Usage:]({})\n" \
             "8. [Total Shards:]({})" \
            .format(servers, n1.strip(), old_errors.strip(), num_cmd.strip(), old_api_calls.strip(), old_date.strip(),
                    bot_memory.strip(), self.bot.shard_count)
        ss_f = '```md\n' + self.bot.DASHES + '\n' + ss + '```'
        await ctx.send(ss_f)

    @commands.is_owner()
    @commands.command(name='shut_down')
    async def shut_down_bot(self, ctx):
        """Will start the bot shutting down. After one minute the bot will be offline."""
        await ctx.send("```fix\n{}```".format("Bot shut down will commence in 60 seconds."))
        await self.bot.get_cog("BackgroundTasks").close()

    @commands.is_owner()
    @commands.command()
    async def check_api(self, ctx):
        usage_info_dict = await self.bot.api.request("getdataused")
        await ctx.send(usage_info_dict)

    @commands.is_owner()
    @commands.command(aliases=['ga'])
    async def get_avatar(self, ctx, player_name):
        """Gets the avatar id currently equipped to a player. Used for figuring out new released avatar id mappings."""
        try:
            info = self.bot.paladinsAPI.getPlayer(player_name)
            # print(info)
            await ctx.send("```fix\n{}```".format(info["AvatarId"]))
        except (PlayerNotFound, PrivatePlayer):
            await ctx.send("Problem finding player.")


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(OwnerCog(bot))
