from discord.errors import HTTPException, Forbidden
from discord import Embed, colour, File
from discord.ext import commands

import aiohttp.client_exceptions as aiohttp_client_exceptions
import concurrent.futures

from socket import gaierror
from io import StringIO
import traceback
import requests
import json

from arez.exceptions import Unauthorized

from my_utils import get_est_time
from colorama import Fore

# Built in discord UI
from MyCustomDiscordView import MyGenericView
from discord import ButtonStyle
from discord.ui import Button


class CommandErrors(commands.Cog):
    """Custom error handling :)"""

    def __init__(self, bot):
        self.bot = bot

        self.error_log_path = "logs/errors"

        self.report_button_timeout = 60

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Lots of error checking for different types of errors."""

        # checks for non-discord command related errors
        if hasattr(error, "original"):
            # print(error.original)
            # Catches connection related exceptions
            if isinstance(error.original, aiohttp_client_exceptions.ClientError) or \
                    isinstance(error.original, gaierror) or \
                    isinstance(error.original, ConnectionError) or isinstance(error.original, TimeoutError) or \
                    isinstance(error.original, requests.exceptions.RequestException) or \
                    isinstance(error.original, concurrent.futures.TimeoutError):
                await self.send_error(cont=ctx, msg="Connection error. Please try again.")
                return None
            elif isinstance(error.original, Forbidden):
                await self.send_error(cont=ctx,
                                      msg="The bot does not have permission to send messages in the channel:"
                                          "\n{} \n\n- where you just called the command:\n{}"
                                      .format(ctx.channel, ctx.message.content))
                return None
            elif isinstance(error.original, MemoryError):
                await self.send_error(cont=ctx,
                                      msg="Your lucky... you caused the bot to run out of memory. Don't worry"
                                          " though... the bot will recover. Please try again.")
                return None
            # Checking different types of ValueError
            elif isinstance(error.original, ValueError):
                try:
                    custom_error, custom_parameter = error.original.args
                except ValueError:
                    custom_error = error.original.args[0]
                    custom_parameter = None
                if str(error.original) == "I/O operation on closed file.":
                    await self.send_error(cont=ctx,
                                          msg="The bot tried to send you a file/image but it has been taken "
                                              "away from the bot...probably because of an internet fluke. "
                                              "Please try again.")
                elif custom_error == "MalformedMatch":
                    await self.send_error(cont=ctx,
                                          msg="Malformed Match!",
                                          msg2="The Paladins API encountered an issue while fetching the match with "
                                               "Id: `{}`.".format(custom_parameter))
                elif custom_error == "InvalidChampName":
                    await self.send_large_error(cont=ctx,
                                                title="Invalid Champion Name: `{}`".format(custom_parameter))
                elif custom_error == "MissingSlashPerms":
                    await self.send_error(cont=ctx,
                                          msg="For this command to work the permission: "
                                              "`Use Application Commands` must be enabled.")
                else:
                    await self.send_error(cont=ctx,
                                          msg=custom_error)
                return None
            elif isinstance(error.original, IndexError):
                if str(error.original) == "MissingName":
                    await self.send_error(cont=ctx,
                                          msg="You provided an empty name... `\"\"`. Please provide a name.")
                    return None
            elif "502 Bad Gateway" in str(error.original):  # New error with the Discord API update
                await self.send_error(cont=ctx, msg="Discord had a connection error. Please try again.")
                return None
            elif "503 Service Unavailable" in str(error.original):  # New error with the Discord API update
                await self.send_error(cont=ctx, msg="Discord had a connection error. Please try again.")
                return None
            elif isinstance(error.original, Unauthorized):
                await self.send_error(cont=ctx, msg="Invalid Paladins Authorization Credentials!",
                                      msg2="The command you are trying to use requires a Paladins API call. "
                                           "Sadly Paladins is not giving out API keys anymore.")
                return None

        # Checks for discord command errors
        if isinstance(error, commands.MissingRequiredArgument):
            await self.send_error(cont=ctx, msg="A required argument to the command you called is missing.")
        elif isinstance(error, HTTPException):  # New error with the Discord API update
            await self.send_error(cont=ctx, msg="Discord itself had a connection error. Please try again.")
        elif isinstance(error, commands.BadArgument):
            await self.send_error(cont=ctx, msg="Make sure the command is in the correct format.")

        # Quote issues
        elif isinstance(error, commands.errors.UnexpectedQuoteError):
            await self.send_error(cont=ctx, msg="If you are trying to type the name Mal`Damba please type his name "
                                                "as one word without any kinda of quote marks.")
        elif isinstance(error, commands.errors.ExpectedClosingQuoteError):
            await self.send_error(cont=ctx, msg=error)
        elif isinstance(error, commands.errors.InvalidEndOfQuotedStringError):
            await self.send_error(cont=ctx, msg=error)

        elif isinstance(error, commands.TooManyArguments):
            await self.send_error(
                cont=ctx,
                msg="Too many arguments passed to a command.",
                msg2="If you are unsure of command's format then type `>>help command_name` to "
                     "learn more about the format of a command.\n\n"
                     "Below are the 2 most common reasons you may have passed extra arguments to a command."
                     "```1. Type all Champion names as one word. So BombKing, ShaLin, and MalDamba.```"
                     "```2. Console names need to by typed with quotes around them and with the platform name. "
                     "For example an Xbox player with the name \"Dark Night\" would do: \"Dark Night Xbox\". "
                     "The platform can be one of the following: Xbox, PS4, Switch, and Epic```")
        elif isinstance(error, commands.CommandNotFound):
            await self.send_error(cont=ctx, msg=error)
        elif isinstance(error, commands.CommandOnCooldown):
            await self.send_error(cont=ctx, msg=error)
        elif isinstance(error, commands.MissingPermissions):
            await self.send_error(cont=ctx, msg=error)
        elif isinstance(error, commands.NotOwner):
            await self.send_error(cont=ctx, msg=error)
        elif isinstance(error, commands.CheckFailure):
            await self.send_error(cont=ctx, msg=error)
        else:
            print(error)
            self.bot.daily_error_count = self.bot.daily_error_count + 1
            print(Fore.RED + "An uncaught error occurred: ", error)  # Log to bot output
            error_file = str(await get_est_time()).replace("/", "-").replace(":", "-").split()
            error_file = "_".join(error_file[::-1])
            error_trace = str(ctx.message.content) + "\n\n"

            # Create string buffer for a .txt file in memory
            str_data = StringIO()
            str_data.write(error_trace)
            traceback.print_exception(type(error), error, error.__traceback__, file=str_data)
            str_data.seek(0)

            msg = "Unfortunately, something messed up. If you entered the command correctly " \
                  "just wait a few seconds and then try again. If the problem occurs again it is " \
                  "most likely a bug that will need to be fixed."

            # Log message directly to discord channel
            server = self.bot.get_guild(537345551520366609)
            channel = server.get_channel(944820585127612528)

            error_embed = Embed(
                title="\N{WARNING SIGN} " + msg + " \N{WARNING SIGN}",
                colour=colour.Color.red(),
            )

            view_ui = MyGenericView(timeout=self.report_button_timeout, author=ctx.author)
            bug_button = Button(style=ButtonStyle.red, label="Submit Bug Report")
            view_ui.add_item(bug_button)

            async def button_callback(interaction):
                """Updates the button and logs/submits the file"""
                # Editor now warns [StringIO()] isn't the right type for fp= but it still works >_>
                await channel.send(file=File(filename=f'{error_file}.txt', fp=str_data))

                bug_button.style = ButtonStyle.green
                bug_button.label = 'Thank You!'
                bug_button.disabled = True

                await interaction.response.edit_message(view=view_ui)

            bug_button.callback = button_callback
            view_ui.message = await ctx.send(embed=error_embed, view=view_ui)

    @staticmethod
    async def send_error(cont, msg, msg2=None):
        """Custom embed error generator. The client will first try to send the error message in the channel
        where it was caused and if that fails it then tries to DM the error to the user."""
        msg = str(msg)
        if not msg2:
            error_embed = Embed(
                title="\N{WARNING SIGN} " + msg + " \N{WARNING SIGN}",
                colour=colour.Color.red(),
            )
        else:
            error_embed = Embed(
                title="\N{WARNING SIGN} " + msg + " \N{WARNING SIGN}",
                description=msg2,
                colour=colour.Color.red(),
            )
        try:  # First lets try to send the message to the channel where the command was invoked
            await cont.send(embed=error_embed)
            # print(Fore.RED + str(msg))
        except Forbidden:
            try:  # Next lets try to DM the message to the user
                author = cont.message.author
                await author.send(embed=error_embed)
                # print(Fore.RED + str(msg))
            except Forbidden:  # Bad sign if we end up here but is possible if the user blocks some DM's
                pass

    @staticmethod
    async def send_large_error(cont, title):
        """Custom embed error generator. The client will first try to send the error message in the channel
        where it was caused and if that fails it then tries to DM the error to the user."""
        with open("cache/all_champions.json", 'r') as FP:
            champ_classes = json.load(FP)

        with open('cache/champ_aliases.json', 'r') as FP:
            champ_aliases = json.load(FP)

        champ_aliases_lookup = {}

        for alias, champ in champ_aliases.items():
            champ_aliases_lookup.setdefault(champ, []).append(alias)

        # Title of embed
        valid_champ_names_embed = Embed(
            title="\N{WARNING SIGN} {} \N{WARNING SIGN}".format(title),
            description="Valid champion names are list below. \n `Please note champion names are not case sensitive. "
                        "\nAll champion names must be typed as one word to make discord happy.`",
            colour=colour.Color.red(),
        )

        # Each champion name for each class
        for champ_type, champs in champ_classes.items():
            valid_champ_names_embed.add_field(name=champ_type.title(),
                                              value="```{}```".format(', '.join(champs)),
                                              inline=False)

        # Each champ and valid aliases
        line = ""
        for champ_name, aliases in champ_aliases_lookup.items():
            line += "{}: {}\n".format(champ_name.replace(' ', ''), ', '.join(aliases))
        valid_champ_names_embed.add_field(name="Champion Aliases", value="```{}```".format(line), inline=False)

        try:  # First lets try to send the message to the channel where the command was invoked
            await cont.send(embed=valid_champ_names_embed)
            # print(Fore.RED + str(title))
        except Forbidden:
            try:  # Next lets try to DM the message to the user
                author = cont.message.author
                await author.send(embed=valid_champ_names_embed)
                # print(Fore.RED + str(title))
            except Forbidden:  # Bad sign if we end up here but is possible if the user blocks some DM's
                pass


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(CommandErrors(bot))
