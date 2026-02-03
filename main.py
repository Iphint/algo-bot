from config import TOKEN
from discord_bot.bot import bot

# register events & commands
import discord_bot.events
import discord_bot.commands

bot.run(TOKEN)