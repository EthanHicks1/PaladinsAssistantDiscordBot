from discord.ext import commands
import discord
import random


# Creates an embed base for the help commands. This way if I every want to change the look of all my help commands
# I can just change the look of all the help commands from this one function.
def create_embed(name, info, pars, des, examples):
    embed = discord.Embed(
        colour=discord.colour.Color.dark_teal()
    )

    embed.add_field(name='Command Name:', value='```md\n' + name + '```', inline=False)
    embed.add_field(name='Description:', value='```fix\n' + info + '```',
                    inline=False)
    format_string = ""
    description_string = ""
    for par, de in zip(pars, des):
        format_string += " <" + par + ">"
        description_string += "<" + par + "> " + de + "\n\n"

    embed.add_field(name='Format:', value='```md\n>>' + name + format_string + '```', inline=False)
    embed.add_field(name='Parameters:', value='```md\n' + description_string + '```', inline=False)

    examples_string = ""
    index = 0
    for example in examples:
        index += 1
        examples_string += "{}. >>{}\n".format(index, example)
    embed.add_field(name='Examples:', value='```md\n' + examples_string + '```', inline=False)

    embed.set_footer(text="Bot created by FeistyJalapeno#9045. Feel free to visit the official bot support server: "
                          "https://discord.gg/njT6zDE to ask questions, provide suggestions, report a bug, etc.",
                     icon_url='https://raw.githubusercontent.com/EthanHicks1/PaladinsArtAssets/master/avatars/0.png')

    return embed


class HelpCog(commands.Cog, name="Help Commands"):
    """Cog that creates help commands for the bot."""

    def __init__(self, bot):
        self.bot = bot

        self.player_names = ['ßones', 'RockMonkey']

    async def get_name(self):
        secure_random = random.SystemRandom()
        return secure_random.choice(self.player_names)

    # Custom help commands
    @commands.group(pass_context=True)
    # @commands.hybrid_group(name='help') // Way too cluttered to show "/help command_name" for every command
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            if ctx.guild is not None:  # If they are already DMing the bot don't show this message
                embed = discord.Embed(
                    description="Check your dms for a full list of commands. For more help on a specific command "
                                "type `>>help <command_name>`",
                    colour=discord.colour.Color.dark_teal()
                )
                await ctx.send(embed=embed)

            author = ctx.message.author
            embed = discord.Embed(
                colour=discord.colour.Color.dark_teal()
            )

            my_message = "Note to get the best experience when using PaladinsAssistant it is recommended that you use "\
                         "discord on desktop since over half of the commands use colors and colors do not show up on " \
                         "Mobile. Below are listed all the different types of commands this bot offers." \
                         "\n\nFor example, if someone " \
                         "wants to know how to use the `stats` command, they would type `>>help stats`" \
                         "\n\nAlso if you want more information on how to use the bot to its full extent, feel free to"\
                         " join the support server here: https://discord.gg/njT6zDE"

            embed.set_author(name='PaladinsAssistant Commands: ')
            # embed.set_thumbnail(url="https://raw.githubusercontent.com/EthanHicks1/PaladinsAssistantBot/master/icons/"
            #                        "miscellaneous/Androxus.png")
            embed.set_footer(icon_url="https://raw.githubusercontent.com/EthanHicks1/PaladinsArtAssets/master/avatars/"
                                      "0.png",
                             text="Bot created by FeistyJalapeno#9045.")
            embed.add_field(name='help', value='Returns this message.', inline=False)
            embed.add_field(name='search', value='Returns info about all players with an account name across platforms.'
                            , inline=False)
            embed.add_field(name='store', value='Stores a player\'s Paladins In Game Name (IGN) for the bot to use.',
                            inline=False)
            embed.add_field(name='unstore', value='Allows players to remove their stored account(s) from the bot '
                                                  'through the use of buttons.',
                            inline=False)
            # Retired 7/17/2022 (finally)
            # embed.add_field(name='last', value='Returns stats for a player\'s match.', inline=False)
            embed.add_field(name='match', value='Returns detailed stats for a player\'s match.', inline=False)
            embed.add_field(name='stats', value='Returns simple overall stats for a player.', inline=False)
            embed.add_field(name='random', value='Allows a user to select different options from a menu to pull a '
                                                 'random selection from (champs, maps, etc).',
                            inline=False)
            embed.add_field(name='current', value='Returns stats for a player\'s current match.', inline=False)
            embed.add_field(name='history', value='Returns simple stats for a up to 50 of a player\'s last matches.',
                            inline=False)
            embed.add_field(name='deck',
                            value='Displayed all the decks for a champion for a specific player in a [menu]. '
                                  'Selecting a deck from the [menu] will create an image of that deck.',
                            inline=False)
            embed.add_field(name='top',
                            value='Prints a sorted list (highest to lowest) of stats of a player\'s champions.',
                            inline=False)
            embed.add_field(name='search',
                            value='Search for players to find their player_id across different platforms.',
                            inline=False)
            embed.add_field(name='server',
                            value='Shows if any of the platforms servers are down.'
                                  'Also shows current steam players for LIVE and PTS.',
                            inline=False)
            embed.add_field(name='set_gm_lb',
                            value='Creates an embed that matches the in game Grandmaster leaderboard '
                                  'that\'s auto updated every two hours.',
                            inline=False)
            embed.add_field(name='prefix',
                            value='Lets the server owner change the prefix of the bot.',
                            inline=False)
            embed.add_field(name='language',
                            value='Lets the server owner change the language the bot uses.',
                            inline=False)
            embed.add_field(name='privacy_policy',
                            value='Displays the privacy policy of the bot.',
                            inline=False)

            # Try to first dm the user the help commands, then try to post it the channel where it was called
            try:
                await author.send(my_message, embed=embed)
            except discord.Forbidden:
                try:
                    await ctx.send(my_message, embed=embed)
                except discord.Forbidden:
                    pass

    @help.command()
    async def store(self, ctx):
        command_name = "store"
        command_description = "Stores a player\'s Paladins In Game Name (IGN) for the bot to use. Once this command " \
                              "is done a player can type the word [me] instead of their name. "
        parameters = ["player_name and platform", "account shortcut"]
        descriptions = ["Player's Paladins IGN and [Optional parameter]: of platform (Xbox, PS4, Epic), defaults to PC",
                        "\n[Optional parameter]: defaults to me, other valid options are me2 and me3"]
        examples = ["{} {}".format(command_name, "ZombieKiller"),
                    "{} {}".format(command_name, "\"Dark Knight Xbox\""),
                    "{} {}".format(command_name, "ZombieKiller2 me2"),
                    "{} {}".format(command_name, "ZombieKiller3 me3")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    async def unstore(self, ctx):
        command_name = "unstore"
        command_description = "Allows players to remove their stored account(s) from the bot through the use of " \
                              "buttons."
        parameters = ["None"]
        descriptions = ["Parameterless command"]
        examples = ["{} {}".format(command_name, "")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    """
    @help.command()
    async def last(self, ctx):
        command_name = "last"
        command_description = "Returns stats for a player\'s last match."
        parameters = ["player_name", "match_id"]
        descriptions = ["Player's Paladins IGN", "The match id of the game. This can be found in game in Paladin's "
                                                 "History tab or in this bots >>history command.\n[Optional parameter]:"
                                                 " if not provided, defaults to most recent match"]
        examples = ["{} {}".format(command_name, "z1unknown"), "{} {}".format(command_name, "z1unknown 012345678")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))
    """

    @help.command()
    async def match(self, ctx):
        command_name = "match"
        command_description = "Returns detailed stats for a player\'s match."
        parameters = ["player_name or match_id", "colored or detailed"]
        descriptions = ["\nPlayer's Paladins IGN\nor \nThe match id of the game. "
                        "This can be found in game in Paladin's History tab or in this bots >>history command.",
                        "If someone wants the text to be colored in the image created by the command then they need to "
                        "type [-c].\n[Optional parameter]: if not provided, defaults to black text \nor\n"
                        "If [-d] is provided then all player names will be printed out along with their self healing "
                        "below the image."]
        examples = ["{} {}".format(command_name, await self.get_name()),
                    "{} {}".format(command_name, "0123456789"),
                    "{} {}".format(command_name, f'{await self.get_name()} -c'),
                    "{} {}".format(command_name, "0123456789 -c"),
                    "{} {}".format(command_name, f'{await self.get_name()} -d'),
                    "{} {}".format(command_name, "0123456789 -d")
                    ]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    async def history(self, ctx):
        command_name = "history"
        command_description = "Returns simple stats for up to 50 of a player\'s last matches."
        parameters = ["player_name", "-c champ_name", "-q queue_name"]
        descriptions = ["Player's Paladins IGN",
                        "champ_name is the champion's name that you want to look for in History\n"
                        "[Optional parameter]: if not provided, defaults to all champions",
                        "queue_name can be one of the following: TDM, Ranked, Onslaught, KOTH, Siege\n"
                        "[Optional parameter]: "
                        "if not provided, defaults to all queue types besides test maps and bot matches"]
        examples = ["{} {}".format(command_name, f'{await self.get_name()}'),
                    "{} {}".format(command_name, f'{await self.get_name()} -q ranked'),
                    "{} {}".format(command_name, f'{await self.get_name()} -c Androxus'),
                    "{} {}".format(command_name, f'{await self.get_name()} -c Androxus -q ranked')]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    async def current(self, ctx):
        command_name = "current"
        command_description = "Get stats for a player's current match."
        parameters = ["player_name", "option"]
        descriptions = ["Player's Paladins IGN", "Type -a if you want an advanced look for all the players. "
                                                 "If -a is provided then the stats of the champion that each person "
                                                 "plays will be returned as well.\n[Optional parameter]: if not "
                                                 "provided, defaults to just returning every player's overall stats"]
        # examples = ["{} {}".format(command_name, "z1unknown")]
        examples = ["{} {}".format(command_name, f'{await self.get_name()}'),
                    "{} {}".format(command_name, "\"Dark Knight xbox\"")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    async def top(self, ctx):
        command_name = "top"
        command_description = "Returns a list of a player\'s champions stats sorted from highest to lowest after " \
                              "selecting an option from a [menu]."
        parameters = ["player_name"]
        descriptions = ["Player's Paladins IGN"]
        examples = ["{} {}".format("top", f'{await self.get_name()}')]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    # ToDo: Remember to update this with buttons once the base command is reworked
    async def search(self, ctx):
        command_name = "search"
        command_description = "Command players can use to look up someone's player_id."
        parameters = ["player_name", "platform_type"]
        option_description = "\n[Optional parameter]: if not provided, defaults to searching across all platforms. " \
                             "It can be one of the following: \n\n" \
                             "1. <Xbox>\n" \
                             "2. <PS4>\n" \
                             "3. <Switch>\n" \
                             "4. <Epic>\n"
        descriptions = ["Player's Paladins IGN", option_description]
        examples = ["{} {}".format(command_name, "iAssassin03"),
                    "{} {}".format(command_name, "iAssassin03 PS4"),
                    "{} {}".format(command_name, "\"Dark Night\" Xbox")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    async def stats(self, ctx):
        command_name = "stats"
        command_description = "Returns simple overall stats for a player."
        parameters = ["player_name", "champ_name"]
        long_string = "<champion_name>: will return the player's stats on the name of the champion typed.\n" \
                      "[Optional parameter]: if not provided, the command defaults to returning the player's overall " \
                      "stats"
        descriptions = ["Player's Paladins IGN", long_string]
        examples = ["{} {}".format(command_name, f'{await self.get_name()}'),
                    "{} {}".format(command_name, f'{await self.get_name()} Viktor')]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    async def random(self, ctx):
        command_name = "random"
        command_description = "Allows a user to select different options from a [menu] to pull a " \
                              "random selection from (champs, maps, etc)."
        parameters = ["None"]
        descriptions = ["Parameterless command"]
        examples = ["{} {}".format(command_name, "")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    async def deck(self, ctx):
        command_name = "deck"
        command_description = 'Displayed all the decks for a champion for a specific player in a [menu]. '\
                              'Selecting a deck from the [menu] will create an image of that deck.'
        parameters = ["player_name", "champ_name"]
        descriptions = ["Player's Paladins IGN ", "Paladin's Champions Name"]
        examples = ["{} {}".format(command_name, f'{await self.get_name()} Androxus')]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    async def set_gm_lb(self, ctx):
        command_name = "set_gm_lb"
        command_description = "Creates an embed that matches the in game Grandmaster leaderboard for PC players " \
                              "that\'s auto updated every two hours. It's recommended you pin the embed produced by " \
                              "this command or run it in a specific limited channel to prevent it from getting buried."
        parameters = ["None"]
        descriptions = ["Parameterless command"]
        examples = ["{} {}".format(command_name, "")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    async def privacy_policy(self, ctx):
        command_name = "privacy_policy"
        command_description = "Displays the privacy policy of the bot."
        parameters = ["None"]
        descriptions = ["Parameterless command"]
        examples = ["{} {}".format(command_name, "")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    """
    @help.command()
    async def console_name(self, ctx):
        command_name = "console_name"
        command_description = "Returns info for how console players should type their name for the bot to recognize."
        parameters = ["None"]
        descriptions = ["Parameterless command"]
        examples = ["{} {}".format(command_name, "")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))
    """

    """ disabled 7/5/2020
    @help.command()
    async def usage(self, ctx):
        command_name = "usage"
        command_description = "Returns how many times you have used commands for this bot."
        parameters = ["None"]
        descriptions = ["Parameterless command"]
        examples = ["{} {}".format(command_name, "")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))
    """

    @help.command()
    async def server(self, ctx):
        command_name = "server"
        command_description = "Shows if any of the platforms servers are down. Also shows current steam players " \
                              "for LIVE and PTS."
        parameters = ["None"]
        descriptions = ["Parameterless command"]
        examples = ["{} {}".format(command_name, "")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    async def bounty(self, ctx):
        command_name = "bounty"
        command_description = "Shows information about the bounty store."
        parameters = ["None"]
        descriptions = ["Parameterless command"]
        examples = ["{} {}".format(command_name, ""), "{} {}".format('bs', "")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    async def prefix(self, ctx):
        command_name = "prefix"
        command_description = "Lets the server owner change the prefix of the bot."
        parameters = ["prefix"]
        descriptions = ["The prefix can be set to whatever you want."]
        examples = ["{} {}".format(command_name, "**")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))

    @help.command()
    async def language(self, ctx):
        command_name = "language"
        command_description = "Lets the server owner change the language the bot uses."
        parameters = ["language"]
        descriptions = ["This command is still being worked on... If you want to bot to use a certain language dm me "
                        "about it. I rely on people translating text, not online translators."]
        examples = ["{} {}".format(command_name, "pl"), "{} {}".format(command_name, "pt"),
                    "{} {}".format(command_name, "fr"), "{} {}".format(command_name, "tr"),
                    "{} {}".format(command_name, "reset")]
        await ctx.send(embed=create_embed(command_name, command_description, parameters, descriptions, examples))


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(HelpCog(bot))
