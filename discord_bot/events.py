import discord # type: ignore
from discord_bot.bot import bot
from services.google_sheet import update_status_by_discord_id
from discord_bot.verify_ui import VerifyView
from discord_bot.templates import get_random_intro
from datetime import datetime, timedelta
import asyncio

pending_intro = {}

@bot.event
async def on_ready():
    bot.add_view(VerifyView()) 
    bot.loop.create_task(check_pending_intro())
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
    intro_channel = discord.utils.get(guild.text_channels, name="kenalan-dulu")
    if intro_channel:
        message = get_random_intro(member.mention)
        await intro_channel.send(message)
    pending_intro[member.id] = {
        "time": datetime.utcnow(),
        "replied": False
    }

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    print("📩 Message:", message.content)
    if message.guild is not None:
        if hasattr(message.channel, "name") and message.channel.name == "kenalan-dulu":
            user_id = message.author.id
            if user_id in pending_intro:
                pending_intro[user_id]["replied"] = True
                print(f"✅ {message.author} sudah intro")

    await bot.process_commands(message)

async def check_pending_intro():
    await bot.wait_until_ready()

    MODERATOR_ID = 943726651399864330

    while not bot.is_closed():
        now = datetime.utcnow()

        for user_id, data in list(pending_intro.items()):
            if data["replied"]:
                continue

            if now - data["time"] > timedelta(hours=24):
            # if now - data["time"] > timedelta(minutes=1):
                user = await bot.fetch_user(user_id)
                moderator = await bot.fetch_user(MODERATOR_ID)

                if user and moderator:
                    from discord_bot.reminder_templates import get_random_reminder

                    message = get_random_reminder(user.name)

                    await moderator.send(
                        f"📩 **Reminder untuk user belum intro**\n\n"
                        f"User: {user.mention}\n"
                        f"Pesan:\n{message}\n\n"
                        f"➡️ Tolong bantu forward ke user ya 🙏"
                    )

                # biar gak spam
                pending_intro[user_id]["replied"] = True

        await asyncio.sleep(600)  # cek tiap 10 menit
        # await asyncio.sleep(20)  # cek tiap 20 detik

@bot.event
async def on_member_remove(member: discord.Member):
    print(f"{member.name} left server")
    update_status_by_discord_id(member.id, "INACTIVE")