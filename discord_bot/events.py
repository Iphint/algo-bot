import discord
from discord_bot.bot import bot
from services.google_sheet import update_status_by_discord_id
from discord_bot.verify_ui import VerifyView

@bot.event
async def on_ready():
    bot.add_view(VerifyView()) 
    print(f"✅ Bot aktif sebagai {bot.user}")

@bot.event  
async def on_member_join(member):
    guild = member.guild
    unverified_role = discord.utils.get(guild.roles, name="Unverified")
    if unverified_role:
        await member.add_roles(unverified_role)
    channel = discord.utils.get(guild.text_channels, name="verify")
    if channel:
        embed = discord.Embed(
            title=f"👋 Selamat datang {member.name}!",
            description=(
                "Silakan klik tombol di bawah untuk memverifikasi akun kamu.\n\n"
                "⚠️ Username & password akan **rahasia** dan hanya kamu yang melihat pesan verifikasi."
            ),
            color=0x2ecc71
        )
        await channel.send(embed=embed, view=VerifyView())

@bot.event
async def on_member_remove(member: discord.Member):
    print(f"{member.name} left server")
    update_status_by_discord_id(member.id, "INACTIVE")