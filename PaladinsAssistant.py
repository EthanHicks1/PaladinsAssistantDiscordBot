from discord.ext import commands
from discord import Intents
import json
from colorama import Fore, init
init(autoreset=True)


class PaladinsAssistant(commands.AutoShardedBot):   # (Converted to AutoShardedBot 8/10/2020)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Removing default help command.
        self.remove_command('help')

        # prefix/language (Guilds)
        self.load_bot_servers_config()

        # Umm, not a big fan of this
        self.command_utils = None

    async def setup_hook(self):
        # Load in setup cog
        await self.load_extension("cogs.core.LoadVars")

        await self.load_extension("cogs.core.BotCoreOverrides")

        # Load Bot cogs
        await self.load_cogs()

        # Store cog instance
        self.command_utils = self.get_cog("CommandUtils")

    # Below cogs represents the folder our cogs are in. The dot is like an import path.
    INITIAL_EXTENSIONS = ['cogs.Help',
                          'cogs.Rand',
                          'cogs.PaladinsAPINew',
                          'cogs.ServersConfig',
                          'cogs.Owner',
                          'cogs.Console',
                          'cogs.DeckImage',
                          'cogs.CurrentMatch',
                          'cogs.MatchHistory',
                          'cogs.MatchImage',
                          'cogs.listeners.GuildJoinRemove',
                          'cogs.listeners.CommandErrors',   # Comment me out to see errors without being caught
                          'cogs.core.BackgroundTasks',
                          'cogs.core.CommandUtils',
                          'cogs.PASlashCommands'
                          ]

    servers_config = {}
    BOT_SERVER_CONFIG_FILE = "cache/server_configs.json"

    # Loads in different server configs (prefix/language)
    def load_bot_servers_config(self):
        with open(self.BOT_SERVER_CONFIG_FILE) as json_f:
            self.servers_config = json.load(json_f)

    def save_bot_servers_config(self):
        with open(self.BOT_SERVER_CONFIG_FILE, 'w') as json_d:
            json.dump(self.servers_config, json_d)

    # Load our extensions(cogs) we have in the list
    async def load_cogs(self):
        for extension in self.INITIAL_EXTENSIONS:
            try:
                await self.load_extension(extension)
                print(Fore.GREEN + "Loaded extension:", Fore.MAGENTA + extension)
            except BaseException as e:
                print(Fore.RED + "Failed to load: {} because of {}".format(extension, e))
        print("")


# Overrides the prefix for the bot to allow for customs prefixes in servers
async def get_prefix(bot, message):
    default_prefix = [bot.PREFIX]
    if message.guild:
        try:
            default_prefix = bot.servers_config[str(message.guild.id)]["prefix"].split(",")
        except KeyError:
            pass
    return commands.when_mentioned_or(*default_prefix)(bot, message)


# Intent stuff required by Discord for October 7th, 2020 update
intents = Intents.all()

# Special Intents that verified bots lose access to if they don't apply for them ---------------------------------------
intents.members = False         # Explicitly Disabled 2/23/2023 -- Required for counting members of a server
intents.presences = True        # Explicitly Enabled            -- Required to see if a user is on mobile
intents.message_content = True  # Explicitly Enabled  2/23/2023 -- Required for our custom error logging

# Some basic Intents that aren't needed
intents.reactions = False
intents.voice_states = False
intents.integrations = False
intents.emojis = False
intents.bans = False

# Creating client for bot
client = PaladinsAssistant(command_prefix=get_prefix, intents=intents, max_messages=0)

# This is kind of lame but I can't be asked to change how this is loaded for now
with open("token.json") as json_file:
    config = json.load(json_file)
    TOKEN = config["discord_token"]

client.run(TOKEN, reconnect=True)
