import discord # type: ignore
from discord.ext import commands # type: ignore
from discord_bot.bot import bot
from services.google_sheet import (
    get_user_log_status,
)
import re
from datetime import datetime, timedelta, timezone

def calculate_metrics(guild, start_date, end_date):

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

    two_months_ago = end_date - timedelta(days=60)

    total_messages = 0
    active_users = set()
    online_users = set()
    last_seen = {}

    for channel in guild.text_channels:
        name = channel.name.lower()

        if not any(k in name for k in KEYWORDS):
            continue

        try:
            async def scan():
                async for msg in channel.history(
                    limit=None,
                    after=two_months_ago,
                    before=end_date
                ):
                    if msg.author.bot:
                        continue

                    uid = msg.author.id

                    if start_date <= msg.created_at.replace(tzinfo=None) <= end_date:
                        active_users.add(uid)

                    online_users.add(uid)

                    total_messages += 1
                    last_seen[uid] = msg.created_at

            import asyncio
            asyncio.run(scan())

        except Exception as e:
            print(f"Error {channel.name}: {e}")

    valid_online_users = len(online_users)

    engagement_depth = round(
        total_messages / len(active_users), 2
    ) if active_users else 0

    engagement_rate = round(
        len(active_users) / valid_online_users, 2
    ) if valid_online_users else 0

    return {
        "total_messages": total_messages,
        "active_users": len(active_users),
        "online_users": valid_online_users,
        "engagement_depth": engagement_depth,
        "engagement_rate": engagement_rate
    }

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
async def progress_range(ctx, *, args):

    if not ctx.guild:
        await ctx.send("❌ Gunakan di server.")
        return

    try:
        match = re.search(
            r"tgl (\d+) bulan (\d+) tahun (\d+) sampai tgl (\d+) bulan (\d+) tahun (\d+)",
            args
        )

        if not match:
            raise ValueError()

        d1, m1, y1, d2, m2, y2 = map(int, match.groups())

        start_date = datetime(y1, m1, d1)
        end_date = datetime(y2, m2, d2) + timedelta(days=1)

    except:
        await ctx.send("❌ Format range salah")
        return

    await ctx.send("⏳ Menghitung range...")

    data = calculate_metrics(ctx.guild, start_date, end_date)

    result = (
        f"📊 **Community Range Report**\n\n"
        f"📅 {d1}-{m1}-{y1} ➜ {d2}-{m2}-{y2}\n\n"

        f"📝 Text Activity\n"
        f"👥 Active Users: {data['active_users']}\n"
        f"👤 Online Users (60d): {data['online_users']}\n"
        f"💬 Total Chats: {data['total_messages']}\n\n"

        f"🔥 Engagement Depth\n"
        f"{data['engagement_depth']} chat/user\n\n"

        f"📊 Engagement Rate\n"
        f"{data['engagement_rate']}\n\n"

        f"⚠️ Inactive (>60 hari) excluded"
    )

    progress_channel = discord.utils.get(ctx.guild.text_channels, name="progress")
    log_channel = discord.utils.get(ctx.guild.text_channels, name="logs")

    if progress_channel:
        await progress_channel.send(result)

    if log_channel:
        await log_channel.send(
            f"📌 {ctx.author.mention} range report\n"
            f"📅 {d1}-{m1}-{y1} ➜ {d2}-{m2}-{y2}"
        )

    await ctx.send("✅ Range report terkirim!")

@bot.command()
@commands.has_any_role("Moderator", "Administrator")
async def progress(ctx, *, args):

    if not ctx.guild:
        await ctx.send("❌ Gunakan di server.")
        return

    try:
        match = re.search(r"tgl (\d+) bulan (\d+) tahun (\d+)", args)
        if not match:
            raise ValueError()

        day, month, year = map(int, match.groups())

        start_date = datetime(year, month, day)
        end_date = start_date + timedelta(days=1)

    except:
        await ctx.send("❌ Format: `!progress tgl 1 bulan 3 tahun 2026`")
        return

    await ctx.send("⏳ Menghitung progress...")

    data = calculate_metrics(ctx.guild, start_date, end_date)

    result = (
        f"📊 **Community Health Report**\n\n"
        f"📅 {day}-{month}-{year}\n\n"

        f"📝 Text Activity\n"
        f"👥 Active Users: {data['active_users']}\n"
        f"👤 Online Users (60d): {data['online_users']}\n"
        f"💬 Total Chats: {data['total_messages']}\n\n"

        f"🔥 Engagement Depth\n"
        f"{data['engagement_depth']} chat/user\n\n"

        f"📊 Engagement Rate\n"
        f"{data['engagement_rate']}\n\n"

        f"⚠️ Inactive (>60 hari) tidak dihitung"
    )

    progress_channel = discord.utils.get(ctx.guild.text_channels, name="progress")
    log_channel = discord.utils.get(ctx.guild.text_channels, name="logs")

    if progress_channel:
        await progress_channel.send(result)

    if log_channel:
        await log_channel.send(
            f"📌 {ctx.author.mention} menjalankan progress\n"
            f"📅 {day}-{month}-{year}"
        )

    await ctx.send("✅ Report terkirim!")