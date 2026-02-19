from discord.ext import commands # type: ignore
from config import intents

bot = commands.Bot(command_prefix="!", intents=intents)