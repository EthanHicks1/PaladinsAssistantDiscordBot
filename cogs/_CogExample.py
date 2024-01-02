from discord.ext import commands


class BaseExample(commands.Cog):
    """Empty Cog Example"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='example', aliases=["ex"])
    async def check_bot(self, ctx):
        await ctx.send("hi")


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(BaseExample(bot))
