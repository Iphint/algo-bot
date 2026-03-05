from discord.ext import commands # type: ignore
from config import intents

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash command synced: {len(synced)}")
    except Exception as e:
        print(e)