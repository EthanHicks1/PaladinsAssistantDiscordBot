from pyrez.exceptions import InvalidArgument
from urllib.request import urlopen
from pyrez.api import PaladinsAPI
from discord.ext import commands
from colorama import Fore
import my_utils
import json
import arez


class LoadVars(commands.Cog):
    """This cog class handles setting up APIs and member/global vars that will be used in the bot in other locations."""

    command_languages = "cache/paladins_api_lang_dict.json"

    def __init__(self, bot):
        self.bot = bot

        self.bot.BOT_CONFIG_FILE = "token.json"
        self.load_bot_config()
        self.load_bot_cmd_languages()
        self.load_avatar_dict()

        # Create class instances to be used throughout the whole bot
        # Adding this try except here so that if someone tries to run the bot without valid Paladins credentials it
        # will still start up
        try:
            self.bot.paladinsAPI = PaladinsAPI(devId=self.bot.ID, authKey=self.bot.KEY)
        except InvalidArgument as IA:
            print(IA)
        self.bot.api = arez.PaladinsAPI(dev_id=self.bot.ID, auth_key=self.bot.KEY)

        self.bot.champs = my_utils.ChampionUtils()

        self.bot.DASHES = "----------------------------------------"
        self.bot.daily_error_count = 0
        self.bot.daily_command_count = 0

        self.bot.BOT_AUTHOR = "FeistyJalapeno#9045"
        self.bot.cached_player_ids = {}
        self.bot.bot_log_file = "logs/bot_log_file.csv"

        self.bot.cached_kbm_gm = {}
        self.bot.cached_controller_gm = {}

        # Servers that have a gm leaderboard msg set up.
        self.bot.gm_lb_cache_pc = 'cache/gm_pc_guilds.json'
        self.bot.gm_lb_pc_data = 'cache/gm_lb_pc.json'

        # Load the json file to find the file extension for an avatar
        with open('cache/avatar_extensions.json', 'r') as FP:
            self.bot.champ_aliases = json.load(FP)

    # Gets important config including sensitive/private info
    def load_bot_config(self):
        with open(self.bot.BOT_CONFIG_FILE) as json_f:
            config = json.load(json_f)
            self.bot.PREFIX = config["prefix"]
            self.bot.ID = config["id"]
            self.bot.KEY = config["key"]
            self.bot.SUPPORT_GUILD_ID = config["guild_id"]

            self.bot.IS_LIVE_BOT = config["is_live_bot"]
            if not self.bot.IS_LIVE_BOT:
                print(Fore.YELLOW + "Bot is in DEV mode and some logging features won't be active.")

            # Private dev guild
            self.bot.DEV_GUILD_ID = config["dev_guild_id"]
            self.bot.DEV_API_ERROR_CHANNEL_ID = config["dev_guild_api_error_channel_id"]
            self.bot.DEV_USER_ERROR_CHANNEL_ID = config["dev_guild_user_error_channel_id"]

    # Loads in different cache translations for text commands
    def load_bot_cmd_languages(self):
        # Loads in language dictionary (need encoding option so it does not mess up other cache)
        with open(self.command_languages, encoding='utf-8') as json_f:
            print(Fore.CYAN + "Loaded language dictionary for PaladinsAPICog...")
            self.bot.cmd_lang_dict = json.load(json_f)

    @staticmethod
    def load_avatar_dict():
        """
        We can directly read/load a json file from a GitHub Repo.
        You should only do something like this from a Github you own or trust.

        Doing something like this has use cases because it can allow for dynamic changes to info without changes to
        the bots code or having to restart the bot. If someone wanted to sync dynamic content from a Github page they
        could make a command to do so or have a background task sync on a time interval.
        """
        url = 'https://raw.githubusercontent.com/EthanHicks1/PaladinsArtAssets/master/avatar_extensions.json'
        response = urlopen(url)
        data = json.loads(response.read())
        with open('cache/avatar_extensions.json', 'w+', encoding='utf-8') as FP:
            json.dump(data, FP, ensure_ascii=False, indent=4)
            print(Fore.CYAN + "Loaded avatar extension dictionary...")


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(LoadVars(bot))
