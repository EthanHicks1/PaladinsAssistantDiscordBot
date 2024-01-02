from discord import Embed, colour
from discord.ext import commands

import requests

# Docs
# https://gist.github.com/AbstractUmbra/a9c188797ae194e592efe05fa129c57f


class PASlashCommands(commands.Cog):
    """Paladins Assistant Hybrid/Slash Commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(description="Displays the privacy policy of the bot.")
    async def privacy_policy(self, ctx):
        """Displays info about different commands to users."""
        main_message = 'Below you will find out what parts/commands of the bot store any type of info on users'

        embed = Embed(
            title='PaladinsAssistant Privacy Policy',
            description=main_message,
            colour=colour.Color.blurple()
        )

        msg_content = 'The only time it does is if you submit a bug report when an uncaught error happens. When you ' \
                      'submit a report, all that\'s logged is the message contents of the command that was run. ' \
                      'For example if you ran the command ">>match player_name" and an error occurred and you ' \
                      'submitted a report. Only ">>match player_name" is put in the error log file. ' \
                      'This info is completely anonymous and can\'t be tracked back to the user and is used to help ' \
                      'track down issues caused by some accounts/paladins data having unusual info.'

        embed.add_field(name='Does PaladinsAssistant ever store any of my message content?',
                        value='```fix\n' + msg_content + '```',
                        inline=False)
        # --------------------------------------------------------------------------------------------------------------

        msg_content = 'It works by storing a paladins account id and mapping it to a specific discord account ' \
                      '(using discord ids). If you ever don\'t want the bot to have this short hand anymore the ' \
                      '>>unstore command can be run to remove this info from the bot.'

        embed.add_field(name='What info does the >>store store on me?',
                        value='```fix\n' + msg_content + '```',
                        inline=False)

        # --------------------------------------------------------------------------------------------------------------

        msg_content = '>>prefix and >>language store a server id and the prefix or lang you set it to. If either of ' \
                      'these wants to be reset the the keyword "reset" can be passed as the parameter to the ' \
                      'command(s). Since both of these commands store info specific to a server, if the bot is ever ' \
                      'kicked from a server it will remove the info, if there was any.'

        embed.add_field(name='What info does the >>prefix and >>language command store?',
                        value='```fix\n' + msg_content + '```',
                        inline=False)

        # --------------------------------------------------------------------------------------------------------------

        msg_content = 'This command work by storing a server id, channel id, and message id to be able to ' \
                      'automatically edit the message (embed) every 2 hours. To remove this info from the bot ' \
                      'simply delete the embed and next time the bot goes to update it, it will see it no longer ' \
                      'exists and remove the stored info for the server.'

        embed.add_field(name='What info does the >>set_gm_lb store?',
                        value='```fix\n' + msg_content + '```',
                        inline=False)

        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Displays server status info.")
    async def server(self, ctx):
        """Displays the server status and how many people are playing through steam and on the PTS."""
        live = requests.get("https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=444090")
        pts = requests.get("https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=596350")
        live_count = live.json()["response"]["player_count"]
        pts_count = pts.json()["response"]["player_count"]

        current_status = await self.bot.api.get_server_status()

        if current_status.all_up:
            server_embed = Embed(
                title="All non PTS servers operational.",
                description="Current Steam players: `{:,}`\n"
                            "Current `PTS` Steam players: `{:,}`".format(live_count, pts_count),
                colour=colour.Color.green(),
            )
            await ctx.send(embed=server_embed)
        else:
            for item in current_status.statuses:
                embed_color = colour.Color.green()

                # Access
                if item.limited_access:
                    sa = "Limited"
                    embed_color = colour.Color.orange()
                else:
                    sa = "Normal"

                # Server up
                if item.up:
                    so = "Yes"
                else:
                    so = "No"
                    embed_color = colour.Color.red()

                server_embed = Embed(
                    title="Server status for {}".format(item.platform.upper()),
                    description="`Server Online: {}\nServer Access: {}`".format(so, sa),
                    colour=embed_color,
                )
                server_embed.set_footer(text="patch: {}".format(item.version))
                await ctx.send(embed=server_embed)


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(PASlashCommands(bot))
