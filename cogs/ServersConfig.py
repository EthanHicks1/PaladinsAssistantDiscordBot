from datetime import datetime, timezone
from discord import Embed, Color
from discord.ext import commands
import json


def server_owner_only():
    """Function decoder that limits a command to only be usable by a server owner."""
    async def predicate(ctx):
        # If in a dm, just return True since we are using this decoder in conjunction with @commands.guild_only()
        if ctx.guild is None:
            return True
        if not ctx.guild.owner_id == ctx.author.id:
            if ctx.guild.owner:
                owner_name = f': `{ctx.guild.owner.name}`'
            else:
                owner_name = ''
            raise NotServerOwner(f'Sorry you are not authorized to use this command. Only the server owner'
                                 f'{owner_name} can use this command.')
        return True
    return commands.check(predicate)


class NotServerOwner(commands.CheckFailure):
    pass


class ServersConfigCog(commands.Cog, name="Servers Config"):
    """Group of commands that should only be run by a server owner."""
    # Different supported languages
    languages = ["Polish", "Português", "French", "Turkish"]
    abbreviations = ["pl", "pt", "fr", "tr"]

    def __init__(self, bot):
        self.bot = bot
        self.gm_lb_guilds = 'cache/gm_lb_guilds.json'

    @commands.command(name='prefix')
    @commands.guild_only()
    @server_owner_only()
    async def set_server_prefix(self, ctx, prefix):
        async with ctx.channel.typing():
            guild_id = str(ctx.guild.id)
            default_prefix = self.bot.PREFIX
            if prefix == default_prefix:
                # Make these embeds
                await ctx.send("You can't set the prefix to the default prefix `{}`.".format(default_prefix))
            elif prefix == "reset":
                if str(guild_id) in self.bot.servers_config and "prefix" in self.bot.servers_config[guild_id]:
                    if "lang" in self.bot.servers_config[guild_id]:
                        self.bot.servers_config[guild_id].pop("prefix")
                    else:
                        self.bot.servers_config.pop(guild_id)

                    await ctx.send("Prefix has been reset to `{}`.".format(default_prefix))
                    # need to update the file now
                    self.bot.save_bot_servers_config()
                else:
                    await ctx.send("Can't reset prefix. It's already the default `{}`.".format(default_prefix))
            else:
                try:
                    self.bot.servers_config[guild_id]["prefix"] = prefix
                except KeyError:  # Server has no configs yet
                    self.bot.servers_config[guild_id] = {}
                    self.bot.servers_config[guild_id]["prefix"] = prefix

                # need to update the file now
                self.bot.save_bot_servers_config()
                await ctx.send("This bot is now set to use the prefix: `" + prefix + "` in this server")

    @commands.command(name='language', aliases=["język"])
    @commands.guild_only()
    @server_owner_only()
    async def set_server_language(self, ctx, language: str):
        async with ctx.channel.typing():
            guild_id = str(ctx.guild.id)
            language = language.lower()

            if language in self.abbreviations:
                try:
                    self.bot.servers_config[guild_id]["lang"] = language
                except KeyError:  # Server has no configs yet
                    self.bot.servers_config[guild_id] = {}
                    self.bot.servers_config[guild_id]["lang"] = language
                # need to update the file now
                self.bot.save_bot_servers_config()
                await ctx.send("This bot is now set to use the language: `" + language + "` in this server")
            elif language == "reset":
                if guild_id in self.bot.servers_config and "lang" in self.bot.servers_config[guild_id]:
                    if "prefix" in self.bot.servers_config[guild_id]:
                        self.bot.servers_config[guild_id].pop("lang")
                    else:
                        self.bot.servers_config.pop(guild_id)

                    await ctx.send("Language has been reset.")
                    # need to update the file now
                    self.bot.save_bot_servers_config()
                else:
                    await ctx.send("Can't reset language. It's already English.")
            else:
                lines = ""
                for abbr, lang, in zip(self.abbreviations, self.languages):
                    lines += "`" + abbr + ":` " + lang + "\n"
                await ctx.send("You entered an invalid language. The available languages are: \n" + lines +
                               "`reset:` Resets the bot to use English"
                               "\nNote that by default the language is English so there is no need to set it to that.")

    @commands.command()
    @commands.guild_only()
    @server_owner_only()
    async def set_gm_lb(self, ctx):
        with open(self.bot.gm_lb_cache_pc) as json_f:
            gm_lb = json.load(json_f)

        guild_id = str(ctx.guild.id)
        if guild_id in gm_lb:   # Server is already tracking the gm lb
            channel_id, msg_id = gm_lb[guild_id].split(':')
            gm_msg = await self.bot.command_utils.get_msg_from_server(server_id=ctx.guild.id,
                                                                      channel_id=channel_id,
                                                                      msg_id=msg_id, is_pc=True)
            if gm_msg:
                await gm_msg.reply(content='Server already tracking the Keyboard leaderboard here.')
        else:
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

                embed = Embed(
                    title='Grandmaster Leaderboard',
                    description='Last Updated: {} UTC'.format(
                        datetime.now(timezone.utc).strftime("%Y-%m-%d `%H:%M:%S`")),
                    colour=Color.dark_teal()
                )

                embed.add_field(name='Top 25', value='```Fix\n' + msg + '```', inline=False)
                embed.add_field(name='26 - 50', value='```\n' + msg2 + '```', inline=False)
                embed.add_field(name='51 - 75', value='```\n' + msg3 + '```', inline=False)
                embed.add_field(name='76 - 100', value='```\n' + msg4 + '```', inline=False)

                msg = await ctx.send(embed=embed)
                self.bot.command_utils.update_stored_messages(server_id=ctx.guild.id,
                                                              channel_id=ctx.channel.id,
                                                              msg_id=msg.id, is_pc=True, add=True)

    @commands.command(name='check')
    async def check_server_language(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.bot.servers_config and "lang" in self.bot.servers_config[guild_id]:
            await ctx.send("This server's language is: " + self.bot.servers_config[guild_id]["lang"])
            return self.bot.servers_config[guild_id]["lang"]
        else:
            await ctx.send("This server's language is English")
            return "English"


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(ServersConfigCog(bot))
