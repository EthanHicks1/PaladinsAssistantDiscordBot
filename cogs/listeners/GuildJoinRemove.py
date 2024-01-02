from discord.errors import Forbidden
from discord.ext import commands

from my_utils import get_est_time


class LogJoinRemove(commands.Cog):
    """Class handles simple logging for when the bot is added or removed from a server."""

    def __init__(self, bot):
        self.bot = bot

        self.server_join_file = "logs/bot_join.csv"
        self.server_remove_file = "logs/bot_remove.csv"

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Sends a simple message to the server owner and logs which server it has joined."""
        try:
            """
            embed = Embed(
                title="PaladinsAssistant",
                description="Thank you for inviting me to your server. "
                            "To learn about my commands please type```>>help```",
                colour=colour.Color.dark_teal(),
            )
            embed.set_thumbnail(
                url="https://raw.githubusercontent.com/EthanHicks1/PaladinsAssistantBot/master/assets/Androxus.png")
            await guild.owner.send(embed=embed)
            """
            pass
        except Forbidden:
            pass

        # Need [Intents.members] to access guild.member_count
        with open(self.server_join_file, '+a') as a_log_file:
            a_log_file.write("{}, {}, {}, {}\n".format(guild, guild.id, 0, await get_est_time()))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """
        Removes the server configs of the server the client was removed from and logs which server it was removed from.

        Reason the client was removed:
            The client got banned.
            The client got kicked.
            The client left the guild.
            The client or the guild owner deleted the guild.
        """

        # When the bot is kicked this will remove server configs if there were any
        if str(guild.id) in self.bot.servers_config:
            self.bot.servers_config.pop(str(guild.id))
            self.bot.save_bot_servers_config()

        # Need [Intents.members] to access guild.member_count
        with open(self.server_remove_file, '+a') as a_log_file:
            a_log_file.write("{}, {}, {}, {}\n".format(guild, guild.id, 0, await get_est_time()))


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(LogJoinRemove(bot))
