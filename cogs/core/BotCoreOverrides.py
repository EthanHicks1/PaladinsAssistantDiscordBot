from discord.ext import commands


class BotCoreOverrides(commands.Cog):
    """Hooking into listeners for logging."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Logged in as:')
        print(self.bot.user.name)
        print(self.bot.DASHES)
        print("Client is fully online and ready to go...")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.bot.daily_command_count = self.bot.daily_command_count + 1


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(BotCoreOverrides(bot))
