import discord # type: ignore
from discord_bot.bot import bot
from services.google_sheet import update_status_by_discord_id, get_user_warning_count, increment_warning, reset_warning
from discord_bot.verify_ui import VerifyView
from discord_bot.templates import get_intro_message
from discord_bot.report_ui import (
    ReportCenterView,
    StudentReportView,
    REPORT_CENTER_CHANNEL,
    STUDENT_REPORT_CHANNEL
)
from discord_bot.profanity_filter import contains_profanity
from discord_bot.spam_filter import check_spam, tracker as spam_tracker
from config import EXEMPT_ROLES, PROFANITY_EXEMPT_IDS, WARNING_ROLES, SPAM_SKIP_CHANNELS
from datetime import datetime, timedelta
import asyncio

pending_intro = {}
last_welcome_check = datetime.utcnow()

NEW_MEMBER_MODERATOR_IDS = [
    943726651399864330, # Arifin
    1407622673130983555, # kak Nad
    1385603832293228658
]

@bot.event
async def on_ready():
    bot.add_view(VerifyView())

    bot.add_view(ReportCenterView())
    bot.add_view(StudentReportView())

    await setup_report_panels()

    bot.loop.create_task(check_pending_intro())
    bot.loop.create_task(auto_welcome_loop())
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

async def notify_moderators_new_member(member):
    for moderator_id in NEW_MEMBER_MODERATOR_IDS:
        try:
            moderator = await bot.fetch_user(moderator_id)

            if moderator and moderator.mutual_guilds:
                await moderator.send(
                    f"👋 **User baru join server**\n\n"
                    f"User: {member.mention}\n"
                    f"Username: `{member}`\n"
                    f"User ID: `{member.id}`\n"
                    f"Server: **{member.guild.name}**\n\n"
                    f"➡️ Mohon pantau proses verifikasi dan intro user ini."
                )

        except Exception as e:
            print(f"❌ Gagal DM moderator {moderator_id}: {e}")

@bot.event  
async def on_member_join(member):
    guild = member.guild
    await notify_moderators_new_member(member)
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
        welcome_msg = get_intro_message([member])
        await intro_channel.send(welcome_msg)

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

        await handle_profanity_filter(message)
        await handle_spam_filter(message)

    await bot.process_commands(message)


async def handle_profanity_filter(message):
    channel_name = message.channel.name.lower()

    if "admin" in channel_name or "mod" in channel_name:
        return

    if message.author.id in PROFANITY_EXEMPT_IDS:
        return

    member_roles = [role.name for role in message.author.roles]
    if any(role in EXEMPT_ROLES for role in member_roles):
        return

    found_words = contains_profanity(message.content)
    if not found_words:
        return

    word_display = ", ".join(found_words)
    warning_count = increment_warning(message.author.id, word_display)

    try:
        await message.delete()
    except Exception:
        pass

    if warning_count <= 3:
        role_name = WARNING_ROLES.get(warning_count)
        role = discord.utils.get(message.guild.roles, name=role_name)

        if role:
            await message.author.add_roles(role)

        desc = f"Kata kasar terdeteksi: `{word_display}`\nPeringatan **{warning_count}/6**"
        if warning_count == 3:
            desc += "\n\n⚠️ **Peringatan terakhir!** Jika diulangi akan di-timeout."
        embed = discord.Embed(description=desc, color=0xffa500)
        await message.channel.send(embed=embed, delete_after=8)

    elif warning_count == 4:
        try:
            timeout_duration = timedelta(days=1)
            await message.author.timeout(timeout_duration, reason="Profanity warning 4 - timeout 1 hari")
        except Exception:
            pass

        desc = f"Kata kasar terdeteksi: `{word_display}`\n⏰ **Timeout 1 hari** diberikan."
        embed = discord.Embed(description=desc, color=0xff4500)
        await message.channel.send(embed=embed, delete_after=10)

    elif warning_count == 5:
        try:
            timeout_duration = timedelta(days=5)
            await message.author.timeout(timeout_duration, reason="Profanity warning 5 - timeout 5 hari")
        except Exception:
            pass

        desc = f"Kata kasar terdeteksi: `{word_display}`\n🔒 **Timeout 5 hari** diberikan."
        embed = discord.Embed(description=desc, color=0xff0000)
        await message.channel.send(embed=embed, delete_after=10)

    elif warning_count >= 6:
        try:
            await message.author.ban(reason="Profanity warning 6 - permanent ban", delete_message_days=0)
            reset_warning(message.author.id)
        except Exception:
            pass

        desc = f"Kata kasar terdeteksi: `{word_display}`\n🚫 **Banned permanen.**"
        embed = discord.Embed(description=desc, color=0x800000)
        await message.channel.send(embed=embed, delete_after=10)


async def handle_spam_filter(message):
    channel_name = message.channel.name.lower()
    if any(skip in channel_name for skip in SPAM_SKIP_CHANNELS):
        return

    if message.author.id in PROFANITY_EXEMPT_IDS:
        return

    member_roles = [role.name for role in message.author.roles]
    if any(role in EXEMPT_ROLES for role in member_roles):
        return

    violations = check_spam(message)
    if not violations:
        return

    severities = [v["severity"] for v in violations]
    types = [v["type"] for v in violations]
    details = [v["detail"] for v in violations]

    detail_text = "\n".join(f"• {d}" for d in details)
    type_summary = ", ".join(types)

    if "high" in severities:
        warning_reason = f"SPAM ({type_summary}): {details[0]}"
        warning_count = increment_warning(message.author.id, warning_reason)

        try:
            await message.delete()
        except Exception:
            pass

        if warning_count <= 3:
            role_name = WARNING_ROLES.get(warning_count)
            role = discord.utils.get(message.guild.roles, name=role_name)
            if role:
                await message.author.add_roles(role)

            desc = (
                f"🚨 **Spam terdeteksi!**\n{detail_text}\n\n"
                f"Peringatan **{warning_count}/6**"
            )
            if warning_count == 3:
                desc += "\n\n⚠️ **Peringatan terakhir!** Jika diulangi akan di-timeout."
            embed = discord.Embed(description=desc, color=0xffa500)
            await message.channel.send(embed=embed, delete_after=8)

        elif warning_count == 4:
            try:
                await message.author.timeout(timedelta(days=1), reason=f"Spam warning 4 - {type_summary}")
            except Exception:
                pass
            desc = f"🚨 **Spam terdeteksi!**\n{detail_text}\n\n⏰ **Timeout 1 hari** diberikan."
            embed = discord.Embed(description=desc, color=0xff4500)
            await message.channel.send(embed=embed, delete_after=10)

        elif warning_count == 5:
            try:
                await message.author.timeout(timedelta(days=5), reason=f"Spam warning 5 - {type_summary}")
            except Exception:
                pass
            desc = f"🚨 **Spam terdeteksi!**\n{detail_text}\n\n🔒 **Timeout 5 hari** diberikan."
            embed = discord.Embed(description=desc, color=0xff0000)
            await message.channel.send(embed=embed, delete_after=10)

        elif warning_count >= 6:
            try:
                await message.author.ban(reason=f"Spam warning 6 - permanent ban", delete_message_days=0)
                reset_warning(message.author.id)
            except Exception:
                pass
            desc = f"🚨 **Spam terdeteksi!**\n{detail_text}\n\n🚫 **Banned permanen.**"
            embed = discord.Embed(description=desc, color=0x800000)
            await message.channel.send(embed=embed, delete_after=10)

    elif "medium" in severities:
        try:
            await message.delete()
        except Exception:
            pass

        warning_reason = f"SPAM ({type_summary}): {details[0]}"
        warning_count = increment_warning(message.author.id, warning_reason)

        role_name = WARNING_ROLES.get(min(warning_count, 3))
        role = discord.utils.get(message.guild.roles, name=role_name)
        if role and warning_count <= 3:
            await message.author.add_roles(role)

        desc = (
            f"⚠️ **Spam terdeteksi!**\n{detail_text}\n\n"
            f"Peringatan **{min(warning_count, 6)}/6**"
        )
        embed = discord.Embed(description=desc, color=0xffa500)
        await message.channel.send(embed=embed, delete_after=8)

    else:
        try:
            await message.delete()
        except Exception:
            pass
        desc = f"ℹ️ **Pesan terlalu spam**\n{detail_text}\n\nHarap tidak mengirim pesan dengan huruf kapital berlebihan."
        embed = discord.Embed(description=desc, color=0xffff00)
        await message.channel.send(embed=embed, delete_after=5)


async def auto_welcome_loop():
    await bot.wait_until_ready()
    global last_welcome_check

    WELCOME_USER_ID = 943726651399864330
    WEBHOOK_NAME = "Arifin"
    _webhook_cache = {}
    first_run = True

    while not bot.is_closed():
        if not first_run:
            await asyncio.sleep(10)  # TODO: ganti ke 7200 setelah testing
        first_run = False
        now = datetime.utcnow()

        for guild in bot.guilds:
            intro_channel = discord.utils.get(guild.text_channels, name="kenalan-dulu")
            if not intro_channel:
                continue

            new_members = []
            for member in guild.members:
                if member.bot:
                    continue
                if member.joined_at:
                    joined = member.joined_at.replace(tzinfo=None)
                    if last_welcome_check <= joined < now:
                        new_members.append(member)

            if not new_members:
                continue

            try:
                user = await bot.fetch_user(WELCOME_USER_ID)
            except Exception:
                continue

            webhook = _webhook_cache.get(guild.id)
            if not webhook:
                for wh in await intro_channel.webhooks():
                    if wh.user and wh.user.id == bot.user.id and wh.name == WEBHOOK_NAME:
                        webhook = wh
                        _webhook_cache[guild.id] = wh
                        break

            if not webhook:
                try:
                    avatar_bytes = await user.avatar.read() if user.avatar else None
                    webhook = await intro_channel.create_webhook(
                        name=WEBHOOK_NAME,
                        avatar=avatar_bytes,
                        reason="Auto welcome webhook",
                    )
                    _webhook_cache[guild.id] = webhook
                except Exception:
                    continue

            template = get_intro_message(new_members)
            try:
                await webhook.send(
                    template,
                    username=user.display_name or WEBHOOK_NAME,
                    avatar_url=user.display_avatar.url,
                )
            except Exception:
                pass

        last_welcome_check = now


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