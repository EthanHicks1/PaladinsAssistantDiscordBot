from discord import NotFound, Embed, colour, File
from discord.ext import commands
import random
import json

import my_utils as helper
from colorama import Fore

# Built in discord UI
from discord import SelectOption, Interaction
from discord.ui import Select

from MyCustomDiscordView import MyGenericView


class RandomCog(commands.Cog, name="Random Commands"):
    """RandomCog"""

    def __init__(self, bot):
        self.bot = bot
        self.load_lang()

    # List of Champs by Class
    DAMAGE_CMD = ["damage", "napastnik", "dano", "dégât"]
    FLANK_CMD = ["flank", "skrzydłowy", "flanco", "flanc"]
    TANK_CMD = ["tank", "frontline", "obrońca", "tanque"]
    SUPPORT_CMD = ["healer", "support", "wsparcie", "suporte", "soutien"]
    CHAMP_CMD = ["champ", "czempion", "campeão", "champion"]
    TEAM_CMD = ["team", "drużyna", "time", "comp", "equipe"]
    MAP_CMD = ["map", "mapa", "carte"]

    # Map Names
    MAPS = ["Frog Isle", "Jaguar Falls", "Serpent Beach", "Frozen Guard", "Ice Mines", "Fish Market", "Timber Mill",
            "Stone Keep", "Brightmarsh", "Splitstone Quarry", "Ascension Peak", "Warder's Gate", "Shattered Desert",
            "Bazaar"]

    lang_dict = {}
    file_name = "cache/random_lang_dict.json"

    def load_lang(self):
        # Loads in language dictionary (need encoding option so it does not mess up other cache)
        with open(self.file_name, encoding='utf-8') as json_f:
            print(Fore.CYAN + "Loaded language dictionary for RandomCog...")

            self.lang_dict = json.load(json_f)

    async def pick_random_champion(self):
        secure_random = random.SystemRandom()
        champ = secure_random.choice(self.bot.champs.ALL_CHAMPS)
        return champ

    async def gen_meme_team(self):
        secure_random = random.SystemRandom()
        champs = secure_random.sample(self.bot.champs.ALL_CHAMPS, 5)
        return champs

    async def gen_team(self):
        sr = random.SystemRandom()
        team = [sr.choice(self.bot.champs.DAMAGES), sr.choice(self.bot.champs.FLANKS),
                sr.choice(self.bot.champs.SUPPORTS), sr.choice(self.bot.champs.TANKS)]

        fill = await self.pick_random_champion()
        """Keep Generating a random champ until its not one we already have"""
        while fill in team:
            fill = await self.pick_random_champion()

        team.append(fill)

        """Shuffle the team so people get different roles"""
        for x in range(random.randint(1, 3)):  # Shuffle a team a random amount of times (1-3)
            random.shuffle(team)

        team_string = "\n"
        for champ in team:
            team_string += champ + "\n"
        return team_string

    class MySelect(Select):
        def __init__(self, options, parent, lang):
            super().__init__(options=options)
            # self.bot = self.bot
            self.parent = parent  # Store instance to parent class lol. This is dumb
            self.lang = lang

        async def callback(self, interaction: Interaction):
            # await interaction.response.send_message(f'You chose: {self.values[0]}')
            secure_random = random.SystemRandom()

            embed = Embed(
                colour=colour.Color.dark_teal()
            )

            current_selection = self.values[0]

            if current_selection == "Damage":
                champ = secure_random.choice(self.parent.bot.champs.DAMAGES)
                embed.add_field(name=self.parent.lang_dict["random_damage"][self.lang], value=champ)
                embed.set_thumbnail(url=await helper.get_champ_image(champ))
                # await client.say(embed=embed)
                await interaction.response.send_message(embed=embed)
            elif current_selection == "Flank":
                champ = secure_random.choice(self.parent.bot.champs.FLANKS)
                embed.add_field(name=self.parent.lang_dict["random_flank"][self.lang], value=champ)
                embed.set_thumbnail(url=await helper.get_champ_image(champ))
                await interaction.response.send_message(embed=embed)
            elif current_selection == "Support":
                champ = secure_random.choice(self.parent.bot.champs.SUPPORTS)
                embed.add_field(name=self.parent.lang_dict["random_healer"][self.lang], value=champ)
                embed.set_thumbnail(url=await helper.get_champ_image(champ))
                await interaction.response.send_message(embed=embed)
            elif current_selection == "Frontline":
                champ = secure_random.choice(self.parent.bot.champs.TANKS)
                embed.add_field(name=self.parent.lang_dict["random_tank"][self.lang], value=champ)
                embed.set_thumbnail(url=await helper.get_champ_image(champ))
                await interaction.response.send_message(embed=embed)
            elif current_selection == "Champion":
                champ = await self.parent.pick_random_champion()
                embed.add_field(name=self.parent.lang_dict["random_champ"][self.lang], value=champ)
                embed.set_thumbnail(url=await helper.get_champ_image(champ))
                await interaction.response.send_message(embed=embed)
            elif current_selection == "Team":
                # async with ctx.channel.typing():
                team = await self.parent.gen_team()
                buffer = await self.parent.bot.get_cog("CurrentCog").\
                    create_team_image(list(filter(None, team.splitlines())), [])
                file = File(filename="Team.png", fp=buffer)
                embed.add_field(name=self.parent.lang_dict["random_team"][self.lang], value=team)
                await interaction.response.send_message(embed=embed, file=file)
            elif current_selection == "Map":
                map_name = secure_random.choice(self.parent.MAPS)
                embed.add_field(name=self.parent.lang_dict["random_map"][self.lang], value=map_name)
                map_name = map_name.lower().replace(" ", "_").replace("'", "")
                m_u = "https://raw.githubusercontent.com/EthanHicks1/PaladinsArtAssets/master/maps/{}.png" \
                    .format(map_name)
                embed.set_image(url=m_u)
                await interaction.response.send_message(embed=embed)
            elif current_selection == "TRI":
                # async with ctx.channel.typing():
                team = await self.parent.gen_meme_team()
                buffer = await self.parent.bot.get_cog("CurrentCog").create_team_image(team, [])
                file = File(filename="Team.png", fp=buffer)
                embed.add_field(name=self.parent.lang_dict["random_team"][self.lang], value="\n".join(team))
                await interaction.response.send_message(embed=embed, file=file)
            """
            elif "set" in command:
                pass
            elif "pick" in command:
                pass
            else:
                await ctx.send(self.lang_dict["random_invalid"][lang])
            """

    # Calls different random functions based on input
    @commands.command(name='rand', aliases=["random", "losuj", "aleatoire", "aléatoire"], ignore_extra=True)
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def rand(self, ctx):
        # Command Vars
        comp_timeout = 60
        lang = await self.bot.command_utils.check_language(ctx=ctx)

        view_ui = MyGenericView(timeout=comp_timeout, author=ctx.author)

        rand_menu = self.MySelect(
            options=[SelectOption(label="Damage", value="Damage"),
                     SelectOption(label="Flank", value="Flank"),
                     SelectOption(label="Frontline", value="Frontline"),
                     SelectOption(label="Support", value="Support"),
                     SelectOption(label="Champion", value="Champion"),
                     SelectOption(label="Team", value="Team"),
                     SelectOption(label="Team (Roles Ignored)", value="TRI"),
                     SelectOption(label="Map", value="Map")],
            parent=self,  # This is stupid but I am also not paid to make this so...
            lang=lang
        )

        view_ui.add_item(rand_menu)

        view_ui.message = await ctx.send(f'This message will self destruct in {comp_timeout} seconds.',
                                         view=view_ui)


# Add this class to the cog list
async def setup(bot):
    await bot.add_cog(RandomCog(bot))
