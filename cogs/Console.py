from arez.exceptions import NotFound, Private, HTTPException
from datetime import date, datetime
from discord import Embed, colour
from discord.ext import commands


class ConsoleCommands(commands.Cog, name="Console Commands"):
    """Holds the command that allows users to search for players accounts."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, aliases=["console", "Console", "Search"], ignore_extra=False)
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def search(self, ctx, player_name):
        """Sends a list of embeds for easy of use for none PC players to be able to store their name in the bot"""
        lang = await self.bot.command_utils.check_language(ctx=ctx)
        async with ctx.channel.typing():
            try:
                players = await self.bot.api.search_players(player_name=player_name, platform=None)
            except NotFound:
                title_text = self.bot.cmd_lang_dict["general_error2"][lang].format(player_name)
                embed = Embed(
                    title=title_text,
                    colour=colour.Color.red()
                )
                await ctx.send(embed=embed)
                return None
            except HTTPException:
                title_text = "Hi-Rez API is down. No data is being returned. Try again in a few hours."
                embed = Embed(
                    title=title_text,
                    colour=colour.Color.red()
                )
                await ctx.send(embed=embed)
                return None

            recent_players = []
            old_players = []
            private_players = []

            msg = f'Found `{len(players)}` player(s) with the name **`{player_name}`**.'

            # Let the user know it could take a while
            if len(players) > 50:
                msg += '\nThis could take a while, please be patient <a:loading:842177005825949717>'

            await ctx.send(msg)

            for player in players:
                try:
                    full_player = await player

                    current_date = date.today()
                    current_time = datetime.min.time()
                    today = datetime.combine(current_date, current_time)

                    last_seen = full_player.last_login
                    if last_seen:
                        last_seen = (today - last_seen).days
                    else:
                        last_seen = 999

                    # only add players seen in the last 90 days
                    if last_seen <= 90:
                        recent_players.append(full_player)
                    else:
                        old_players.append(full_player)
                except Private:
                    private_players.append(player)

            # Todo: In the future format this to just be a list since we have already processed the accounts
            if len(recent_players) > 10:
                await ctx.send(
                            "```There are too many players ({} recent and {} old accounts) with the name "
                            "{}:\n\nPlease look on PaladinsGuru to "
                            "find the Player ID```https://paladins.guru/search?term={}&type=Player"
                            .format(len(recent_players), len(old_players), player_name, player_name.replace(" ", "%20"))
                )
                return None

            if len(recent_players) == 0:
                await ctx.send("Found `0` recent player(s) `(seen in the last 90 days)`.\n"
                               "Found `{}` old player(s).\n"
                               "Found `{}` private player(s).\n".format(len(old_players), len(private_players)))
                if len(private_players) > 0:
                    for pp in private_players:
                        await ctx.send(f'||`{pp.name}` {pp.id} `{pp.platform}`||')

            else:
                await ctx.send("Found `{}` recent player(s) `(seen in the last 90 days)`".format(len(recent_players)))

            for player in recent_players:
                current_date = date.today()
                current_time = datetime.min.time()
                today = datetime.combine(current_date, current_time)

                last_seen = player.last_login
                last_seen = (today - last_seen).days
                if last_seen <= 0:
                    last_seen = "Today"
                else:
                    last_seen = "{} days ago".format(last_seen)

                embed = Embed(
                    title=player.name,
                    description="↓↓↓  Player ID  ↓↓↓```fix\n{}```".format(player.id),
                    colour=colour.Color.dark_teal(),
                )
                embed.add_field(name='Last Seen:', value=last_seen, inline=True)
                embed.add_field(name='Account Level:', value=player.level, inline=True)
                embed.add_field(name='Hours Played:', value=str(int(player.playtime.total_hours())), inline=True)
                embed.add_field(name='Account Created:', value=player.created_at, inline=True)
                embed.add_field(name='Platform:', value=player.platform, inline=True)

                # get the extension if it exists
                ext = self.bot.champ_aliases.get(str(player.avatar_id))

                # create the avatar_name (name.extension)
                if ext is None:
                    avatar_name = "0.png"  # couldn't find the avatar
                else:
                    avatar_name = str(player.avatar_id) + "." + ext

                embed.set_thumbnail(url="https://raw.githubusercontent.com/EthanHicks1/PaladinsArtAssets/master/"
                                        "avatars/{}".format(avatar_name))

                await ctx.send(embed=embed)


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(ConsoleCommands(bot))
