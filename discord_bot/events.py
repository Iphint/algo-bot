import discord # type: ignore
from discord_bot.bot import bot
from services.google_sheet import update_status_by_discord_id
from discord_bot.verify_ui import VerifyView
from discord_bot.templates import get_random_intro
from discord_bot.report_ui import (
    ReportCenterView,
    StudentReportView,
    REPORT_CENTER_CHANNEL,
    STUDENT_REPORT_CHANNEL
)
from datetime import datetime, timedelta
import asyncio

pending_intro = {}

@bot.event
async def on_ready():
    bot.add_view(VerifyView())

    bot.add_view(ReportCenterView())
    bot.add_view(StudentReportView())

    await setup_report_panels()

    bot.loop.create_task(check_pending_intro())
    print(f"✅ Bot aktif sebagai {bot.user}")

async def setup_report_panels():
    for guild in bot.guilds:
        report_center = discord.utils.get(
            guild.text_channels,
            name=REPORT_CENTER_CHANNEL
        )

        student_reports = discord.utils.get(
            guild.text_channels,
            name=STUDENT_REPORT_CHANNEL
        )

        if report_center:
            await ensure_report_center_panel(report_center)

        if student_reports:
            await ensure_student_report_panel(student_reports)


async def ensure_report_center_panel(channel):
    async for message in channel.history(limit=20):
        if message.author == bot.user and message.embeds:
            if message.embeds[0].title == "🛡️ Algonova Safety Report Center":
                return

    embed = discord.Embed(
        title="🛡️ Algonova Safety Report Center",
        description=(
            "Gunakan tombol di bawah untuk melaporkan hal mencurigakan.\n\n"
            "Contoh:\n"
            "🚨 Spam crypto\n"
            "🔐 Akun kena hack\n"
            "🔗 Scam link\n"
            "👤 Impersonation\n\n"
            "Laporan akan masuk ke spreadsheet sheet `report-center`."
        ),
        color=0xe74c3c
    )

    await channel.send(embed=embed, view=ReportCenterView())


async def ensure_student_report_panel(channel):
    async for message in channel.history(limit=20):
        if message.author == bot.user and message.embeds:
            if message.embeds[0].title == "🎓 Algonova Student Report Center":
                return

    embed = discord.Embed(
        title="🎓 Algonova Student Report Center",
        description=(
            "Gunakan tombol di bawah untuk melaporkan kendala akun siswa.\n\n"
            "Contoh:\n"
            "🔐 Tidak bisa login\n"
            "🔑 Lupa password\n"
            "🏷️ Salah role\n"
            "✅ Gagal verifikasi\n"
            "🚪 Tidak bisa akses channel\n\n"
            "Laporan akan masuk ke spreadsheet sheet `student-reports`."
        ),
        color=0x3498db
    )

    await channel.send(embed=embed, view=StudentReportView())

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