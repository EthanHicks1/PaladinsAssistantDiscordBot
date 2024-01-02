<div align="center">

# Paladins Assistant

<a href="https://github.com/EthanHicks1/PaladinsAssistantBot" title="Paladins Assistant" alt="Paladins Assistant"><img src="icons/miscellaneous/Androxus.png" height="200" width="200"></a>

[![Discord Server](https://img.shields.io/discord/554372822739189761.svg?style=plastic&logo=discord&logoWidth=15)](https://discord.gg/njT6zDE "Support Server · Discord")
![Static Badge](https://img.shields.io/badge/Python-3.8-blue?logo=python&logoColor=yellow&link=https%3A%2F%2Fwww.python.org%2F "Python Runtime Version")
![Static Badge](https://img.shields.io/badge/discord.py-2.3-blue?logo=python&logoColor=yellow&link=https%3A%2F%2Fdiscordpy.readthedocs.io%2Fen%2Flatest%2Findex.html "Discord.py Docs")

### A powerful and unique Discord Bot for getting statistics on [*Paladins*](https://www.paladins.com "Paladins Game") players.
</div>

> [!IMPORTANT]
> The purpose of having this bot's code now public is so it can be used as a learning resource. To understand some coding concepts used within this bot it's assumed you have a basic understand of both `Python 3` and the Python Discord Wrapper `Discord.py`.

## Getting Started
Clone this GitHub repo using whatever method you prefer. Next install all the necessary libraries however you prefer (either one by one or using `requirements.txt`). Again this repo is not for beginners. There are plenty of online resources for setting up a discord bot if you need help.

To get the bot to actually run correctly, you will need to copy the file: `token_example.json` and rename the copy to: `token.json` and then update most of the variables inside it. Below is an explanation of what each config parameter does.
- `discord_token` (Your Discord Bot Token)
- `prefix` (What default prefix you want the bot to have)
- `id` (Paladins API ID)
- `key` (Paladins API KEY)
- `is_live_bot` (In general it's good practice when developing a public discord bot to have two separate versions of the bot so when you are making changes you are not messing with the version people are using. Setting this to true enables some background tasks.)
- `guild_id` (Whatever guild ID this points too will be what bot uses to count the online members.)

- `dev_guild_id` (Development Guild ID of where you are messing with this bot.)
- `dev_guild_api_error_channel_id` (Specific Channel ID in your above server for Paladins API Errors.)
- `dev_guild_user_error_channel_id` (Specific Channel ID in your above server for self reported User Errors. This can be the same ID as above if wanted.)


> [!WARNING]
> If you would like to contribute code (specifically new commands or features) to the bot while it's still active. Please join the [discord support server](https://discord.gg/njT6zDE) before submitting a pull request, so the feature can be discussed beforehand. Go to the #role-menu channel and react with the lock symbol to give yourself the programmer role.

## API Wrappers Used
Paladins Assistant uses the Python Discord wrapper [Discord.py](https://github.com/Rapptz/discord.py) to connect to the [Discord API](https://discord.gg/discord-api).

Paladins Assistant uses the wrapper [Pyrez](https://github.com/luissilva1044894/Pyrez) and [aRez](https://github.com/DevilXD/aRez) to access the [*Hi-Rez Studios*](http://www.hirezstudios.com "Hi-Rez Studios") Paladins API.


## Legacy Contributors
Code: [`@Luís`](https://github.com/luissilva1044894 "Luís")

Code: [`@DevilXD`](https://github.com/DevilXD "DevilXD")

Bot Logo: [`@Lockness4`](https://www.instagram.com/xxsilenceisgoldenxx "SilenceIsGolden")

## Paladins License
All information obtained is provided by Hi-Rez Studios API and is thus their property. According to Section 11a of the API Terms of Use, you must attribute any data provided as below.

> Data provided by Hi-Rez. © 2024 Hi-Rez Studios, Inc. All rights reserved.
