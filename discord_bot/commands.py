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

    try:
        match = re.search(r"tgl (\d+) bulan (\d+) tahun (\d+)", args)
        if not match:
            raise ValueError("Format salah")

        day, month, year = map(int, match.groups())

        WIB = timezone(timedelta(hours=7))
        target_date = datetime(year, month, day, tzinfo=WIB)
        next_day = target_date + timedelta(days=1)

    except:
        await ctx.send("❌ Format salah!\n`!progress tgl 27 bulan 4 tahun 2026`")
        return

    await ctx.send("⏳ Menghitung data...")

    guild = ctx.guild

    TEXT_CHANNELS = [
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
        if channel.name not in TEXT_CHANNELS:
            continue

        try:
            async for message in channel.history(limit=None, after=target_date, before=next_day):
                if message.author.bot:
                    continue

                total_messages += 1
                active_users.add(message.author.id)

        except Exception as e:
            print(f"Error {channel.name}:", e)

    # 🔊 VOICE DATA
    voice_users = 0
    voice_events = 0

    target_day = target_date.date()

    if target_day in voice_activity:
        voice_users = len(voice_activity[target_day]["users"])
        voice_events = voice_activity[target_day]["events"]

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

    await ctx.send("✅ Report dikirim ke #progress")


@progress.error
async def progress_error(ctx, error):
    from discord.ext import commands

    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("❌ Hanya Moderator/Admin yang bisa pakai command ini.")