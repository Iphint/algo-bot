import discord # type: ignore
from discord.ext import commands # type: ignore
from discord_bot.bot import bot
from services.google_sheet import (
    get_user_log_status,
)
import re
from datetime import datetime, timedelta, timezone
from discord_bot.events import voice_activity

@bot.command()
async def test(ctx):
    print("TEST COMMAND CALLED")
    await ctx.send("✅ Test berhasil!")

@bot.command()
@commands.has_permissions(administrator=True)
async def recheck(ctx):
    guild = ctx.guild
    count = 0

    for member in guild.members:
        if member.bot:
            continue

        status = get_user_log_status(member.id)

        if status == "ACTIVE":
            verified_role = discord.utils.get(guild.roles, name="Verified")
            if verified_role and verified_role not in member.roles:
                await member.add_roles(verified_role)
                count += 1

    await ctx.send(f"✅ Recheck selesai. {count} member diperbaiki.")

@bot.command()
@commands.has_role("Moderator")
async def sendverify(ctx):
    from discord_bot.verify_ui import VerifyView

    embed = discord.Embed(
        title="🎓 Student Verification",
        description="Klik tombol di bawah untuk verifikasi akun kamu.",
        color=0x2ecc71
    )

    await ctx.send(embed=embed, view=VerifyView())

@bot.command()
@commands.has_any_role("Moderator", "Administrator")
async def progress(ctx, *, args):
    print("🔥 PROGRESS COMMAND TRIGGERED")

    if not ctx.guild:
        await ctx.send("❌ Gunakan command ini di server.")
        return

    # 🔍 PARSING
    try:
        match = re.search(r"tgl (\d+) bulan (\d+) tahun (\d+)", args)
        if not match:
            raise ValueError("Format salah")

        day, month, year = map(int, match.groups())

        # ⚠️ FIX: pakai UTC tanpa timezone biar gak miss data
        target_date = datetime(year, month, day)
        next_day = target_date + timedelta(days=1)

    except Exception as e:
        print("❌ Parsing error:", e)
        await ctx.send("❌ Format salah!\n`!progress tgl 27 bulan 4 tahun 2026`")
        return

    await ctx.send("⏳ Menghitung data...")

    guild = ctx.guild

    # 🎯 CHANNEL FILTER (SAFE FUZZY MATCH)
    KEYWORDS = [
        "global-chat",
        "showcase",
        "competition",
        "meme-corner",
        "main-chat",
        "weekly-quest",
        "fun-activity",
        "kenalan-dulu"
    ]

    total_messages = 0
    active_users = set()

    for channel in guild.text_channels:
        name = channel.name.lower()

        if not any(k in name for k in KEYWORDS):
            continue

        print(f"🔍 scanning channel: {channel.name}")

        try:
            async for message in channel.history(
                limit=None,
                after=target_date,
                before=next_day
            ):
                if message.author.bot:
                    continue

                total_messages += 1
                active_users.add(message.author.id)

        except Exception as e:
            print(f"❌ error {channel.name}: {e}")

    # 🔊 VOICE DATA
    voice_users = 0
    voice_events = 0

    if target_date.date() in voice_activity:
        voice_users = len(voice_activity[target_date.date()]["users"])
        voice_events = voice_activity[target_date.date()]["events"]

    # 📊 RESULT
    result = (
        f"📊 **Progress Komunitas**\n\n"
        f"📅 {day}-{month}-{year}\n\n"

        f"📝 Text Activity\n"
        f"👥 User aktif: {len(active_users)}\n"
        f"💬 Total pesan: {total_messages}\n\n"

        f"🔊 Voice Activity\n"
        f"👥 User join: {voice_users}\n"
        f"🔁 Event: {voice_events}\n\n"

        f"🔥 Engagement: "
        f"{round(total_messages / len(active_users), 2) if active_users else 0}"
    )

    # 📤 SEND TO CHANNELS
    progress_channel = discord.utils.get(guild.text_channels, name="progress")
    log_channel = discord.utils.get(guild.text_channels, name="logs")

    if progress_channel:
        await progress_channel.send(result)
    else:
        await ctx.send("❌ Channel #progress tidak ditemukan.")

    if log_channel:
        await log_channel.send(
            f"📌 {ctx.author.mention} menjalankan progress\n"
            f"📅 {day}-{month}-{year}"
        )

    await ctx.send("✅ Report berhasil dikirim!")