import discord # type: ignore
from discord.ext import commands # type: ignore
from discord_bot.bot import bot
from services.google_sheet import (
    get_user_log_status,
)
import re
from datetime import datetime, timedelta, timezone

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
@commands.has_any_role("Moderator", "Administrator")
async def progress(ctx, *, args):
    print("🔥 PROGRESS COMMAND TRIGGERED")

    if not ctx.guild:
        await ctx.send("❌ Gunakan command ini di server.")
        return

    from services.google_sheet import append_progress_report

    guild = ctx.guild

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

    # =========================
    # PARSE INPUT: SINGLE / RANGE
    # =========================
    try:
        is_range = "sampai" in args.lower()

        if is_range:
            match = re.search(
                r"tgl (\d+) bulan (\d+) tahun (\d+) sampai tgl (\d+) bulan (\d+) tahun (\d+)",
                args
            )

            if not match:
                raise ValueError("Format range salah")

            d1, m1, y1, d2, m2, y2 = map(int, match.groups())

            start_date = datetime(y1, m1, d1)
            end_date = datetime(y2, m2, d2) + timedelta(days=1)

            date_label = f"{d1}-{m1}-{y1} ➜ {d2}-{m2}-{y2}"
            report_type = "RANGE"

        else:
            match = re.search(r"tgl (\d+) bulan (\d+) tahun (\d+)", args)

            if not match:
                raise ValueError("Format harian salah")

            d, m, y = map(int, match.groups())

            start_date = datetime(y, m, d)
            end_date = start_date + timedelta(days=1)

            date_label = f"{d}-{m}-{y}"
            report_type = "DAILY"

    except Exception as e:
        print("❌ Parsing error:", e)
        await ctx.send(
            "❌ Format salah!\n\n"
            "📌 Harian:\n"
            "`!progress tgl 18 bulan 5 tahun 2026`\n\n"
            "📌 Range:\n"
            "`!progress tgl 1 bulan 5 tahun 2026 sampai tgl 18 bulan 5 tahun 2026`"
        )
        return

    await ctx.send("⏳ Menghitung progress komunitas...")

    # =========================
    # SCAN ACTIVITY SESUAI RANGE COMMAND
    # =========================
    total_messages = 0
    active_users_range = set()
    user_message_count = {}

    for channel in guild.text_channels:
        name = channel.name.lower()

        if not any(k in name for k in KEYWORDS):
            continue

        try:
            async for message in channel.history(
                limit=None,
                after=start_date,
                before=end_date
            ):
                if message.author.bot:
                    continue

                uid = message.author.id

                total_messages += 1
                active_users_range.add(uid)
                user_message_count[uid] = user_message_count.get(uid, 0) + 1

        except Exception as e:
            print(f"❌ Error scan range {channel.name}: {e}")

    # =========================
    # SCAN USER AKTIF 90 HARI
    # NOTE: Discord tidak menyediakan history online/offline.
    # Jadi active = pernah chat dalam 90 hari.
    # =========================
    now = datetime.utcnow()
    cutoff_90d = now - timedelta(days=90)
    cutoff_60d = now - timedelta(days=60)

    active_users_90d = set()
    active_users_60d = set()

    for channel in guild.text_channels:
        name = channel.name.lower()

        if not any(k in name for k in KEYWORDS):
            continue

        try:
            async for message in channel.history(
                limit=None,
                after=cutoff_90d
            ):
                if message.author.bot:
                    continue

                active_users_90d.add(message.author.id)

                if message.created_at.replace(tzinfo=None) >= cutoff_60d:
                    active_users_60d.add(message.author.id)

        except Exception as e:
            print(f"❌ Error scan 90d {channel.name}: {e}")

    # =========================
    # AMBIL SEMUA MEMBER NON BOT
    # =========================
    all_members = [
        member for member in guild.members
        if not member.bot
    ]

    all_member_ids = set(member.id for member in all_members)

    inactive_users_90d = all_member_ids - active_users_90d

    # =========================
    # LIST NAMA USER
    # =========================
    active_user_names = []
    inactive_user_names = []

    for uid in active_users_90d:
        member = guild.get_member(uid)
        if member:
            active_user_names.append(member.display_name)

    for uid in inactive_users_90d:
        member = guild.get_member(uid)
        if member:
            inactive_user_names.append(member.display_name)

    active_user_names.sort()
    inactive_user_names.sort()

    # =========================
    # METRICS
    # =========================
    engagement_depth = (
        round(total_messages / len(active_users_range), 2)
        if active_users_range else 0
    )

    active_rate_60d = (
        round((len(active_users_range) / len(active_users_60d)) * 100, 2)
        if active_users_60d else 0
    )

    if engagement_depth <= 2:
        engagement_label = "🔴 LOW DEPTH"
    elif engagement_depth <= 7:
        engagement_label = "🟡 MEDIUM DEPTH"
    else:
        engagement_label = "🟢 HIGH DEPTH"

    engagement_score = min(100, int(engagement_depth * 10))

    # =========================
    # DISCORD RESULT
    # =========================
    active_preview = "\n".join([f"- {name}" for name in active_user_names[:15]])
    inactive_preview = "\n".join([f"- {name}" for name in inactive_user_names[:15]])

    if len(active_user_names) > 15:
        active_preview += f"\n... dan {len(active_user_names) - 15} user lainnya"

    if len(inactive_user_names) > 15:
        inactive_preview += f"\n... dan {len(inactive_user_names) - 15} user lainnya"

    result = (
        f"📊 **Progress Komunitas**\n\n"
        f"📅 **Periode:** {date_label}\n\n"

        f"📝 **Text Activity**\n"
        f"💬 Total pesan: **{total_messages}**\n"
        f"👥 User aktif di periode ini: **{len(active_users_range)}**\n\n"

        f"👥 **User Health**\n"
        f"🟢 Active users 90 hari: **{len(active_users_90d)}**\n"
        f"🔴 Inactive users 90 hari: **{len(inactive_users_90d)}**\n\n"

        f"📈 **Engagement Analysis**\n"
        f"🔥 Engagement Depth: **{engagement_depth} pesan/user aktif periode**\n"
        f"📊 Active Rate 60d: **{active_rate_60d}%**\n"
        f"📊 Status: {engagement_label}\n"
        f"🎯 Health Score: **{engagement_score}/100**\n\n"

        f"🟢 **Active User Preview**\n"
        f"{active_preview if active_preview else '-'}\n\n"

        f"🔴 **Inactive User Preview**\n"
        f"{inactive_preview if inactive_preview else '-'}\n\n"

        f"📌 Full list sudah dikirim ke spreadsheet `progress-reports`."
    )

    progress_channel = discord.utils.get(guild.text_channels, name="progress")
    log_channel = discord.utils.get(guild.text_channels, name="logs")

    if progress_channel:
        await progress_channel.send(result)
    else:
        await ctx.send("❌ Channel #progress tidak ditemukan.")

    if log_channel:
        await log_channel.send(
            f"📌 {ctx.author.mention} menjalankan progress report\n"
            f"📅 {date_label}\n"
            f"🔥 Depth: {engagement_depth}\n"
            f"🟢 Active 90d: {len(active_users_90d)}\n"
            f"🔴 Inactive 90d: {len(inactive_users_90d)}"
        )
    
    append_progress_report({
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "report_type": report_type,
        "date_range": date_label,
        "total_messages": total_messages,
        "active_users_range": len(active_users_range),
        "active_users_90d": len(active_users_90d),
        "inactive_users_90d": len(inactive_users_90d),
        "engagement_depth": engagement_depth,
        "active_rate_60d": f"{active_rate_60d}%",
        "score": engagement_score,
        "active_user_list": ", ".join(active_user_names),
        "inactive_user_list": ", ".join(inactive_user_names),
        "executed_by": str(ctx.author),
    })

    await ctx.send("✅ Progress report berhasil dikirim ke #progress dan spreadsheet.")

@bot.command()
@commands.has_any_role("Moderator", "Administrator")
async def joined(ctx, *args):
    print("🔥 JOINED FROM WELCOME CHANNEL TRIGGERED")

    if not ctx.guild:
        await ctx.send("❌ Gunakan command ini di server.")
        return

    try:
        if len(args) == 1:
            d, m, y = map(int, args[0].split("-"))
            start_date = datetime(y, m, d)
            end_date = start_date + timedelta(days=1)
            date_label = args[0]

        elif len(args) == 2:
            d1, m1, y1 = map(int, args[0].split("-"))
            d2, m2, y2 = map(int, args[1].split("-"))

            start_date = datetime(y1, m1, d1)
            end_date = datetime(y2, m2, d2) + timedelta(days=1)
            date_label = f"{args[0]} ➜ {args[1]}"

        else:
            raise ValueError("Format salah")

    except Exception:
        await ctx.send(
            "❌ Format salah!\n\n"
            "Gunakan:\n"
            "`!joined 18-5-2026`\n"
            "atau\n"
            "`!joined 1-5-2026 18-5-2026`"
        )
        return

    welcome_channel = discord.utils.find(
        lambda c: "welcome" in c.name.lower(),
        ctx.guild.text_channels
    )

    if not welcome_channel:
        available_channels = ", ".join(
            [c.name for c in ctx.guild.text_channels[:30]]
        )

        await ctx.send(
            "❌ Channel welcome tidak ditemukan.\n\n"
            f"Channel yang terbaca bot:\n`{available_channels}`"
        )
        return

    await ctx.send("⏳ Menghitung data join dan respond welcome...")

    total_join = 0
    joined_users = set()
    respond_users = set()

    try:
        async for message in welcome_channel.history(
            limit=None,
            after=start_date,
            before=end_date
        ):
            # pesan welcome dari bot
            if message.author.bot:
                total_join += 1

                for user in message.mentions:
                    if not user.bot:
                        joined_users.add(user.display_name)

            # balasan user di welcome
            else:
                respond_users.add(message.author.display_name)

    except Exception as e:
        print(f"❌ Error scan welcome: {e}")
        await ctx.send("❌ Gagal scan channel welcome.")
        return

    total_respond = len(respond_users)
    not_respond = max(total_join - total_respond, 0)

    response_rate = (
        round((total_respond / total_join) * 100, 2)
        if total_join > 0
        else 0
    )

    respond_list = sorted(list(respond_users))

    respond_preview = "\n".join(
        [f"- {name}" for name in respond_list[:20]]
    )

    if len(respond_list) > 20:
        respond_preview += f"\n... dan {len(respond_list) - 20} user lainnya"

    result = (
        f"📥 **Joined Student Report**\n\n"
        f"📅 Periode: **{date_label}**\n"
        f"📍 Source: {welcome_channel.mention}\n\n"

        f"👥 **Join Activity**\n"
        f"➡️ Total Join: **{total_join}**\n\n"

        f"🙋 **Welcome Engagement**\n"
        f"✅ Respond Welcome: **{total_respond}**\n"
        f"💤 Tidak Respond: **{not_respond}**\n"
        f"📊 Respond Rate: **{response_rate}%**\n\n"

        f"📋 **User yang Respond:**\n"
        f"{respond_preview if respond_preview else '-'}"
    )

    progress_channel = discord.utils.get(
        ctx.guild.text_channels,
        name="progress"
    )

    if progress_channel:
        await progress_channel.send(result)
        await ctx.send("✅ Joined report berhasil dikirim ke #progress.")
    else:
        await ctx.send(result)


@bot.command()
@commands.has_any_role("Moderator", "Administrator")
async def intro_stats(ctx, *args):
    print("🔥 INTRO STATS TRIGGERED")

    if not ctx.guild:
        await ctx.send("❌ Gunakan command ini di server.")
        return

    raw_args = " ".join(args).strip()

    try:
        if not raw_args:
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()
            date_label = "7 hari terakhir"
        else:
            match_words_range = re.search(
                r"tgl (\d+) bulan (\d+) tahun (\d+) sampai tgl (\d+) bulan (\d+) tahun (\d+)",
                raw_args.lower()
            )
            match_words_single = re.search(
                r"tgl (\d+) bulan (\d+) tahun (\d+)",
                raw_args.lower()
            )
            date_matches = re.findall(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", raw_args)

            if match_words_range:
                d1, m1, y1, d2, m2, y2 = map(int, match_words_range.groups())
                start_date = datetime(y1, m1, d1)
                end_date = datetime(y2, m2, d2) + timedelta(days=1)
                date_label = f"{d1}-{m1}-{y1} ➜ {d2}-{m2}-{y2}"
            elif match_words_single:
                d, m, y = map(int, match_words_single.groups())
                start_date = datetime(y, m, d)
                end_date = start_date + timedelta(days=1)
                date_label = f"{d}-{m}-{y}"
            elif len(date_matches) >= 2:
                d1, m1, y1 = map(int, date_matches[0])
                d2, m2, y2 = map(int, date_matches[1])
                start_date = datetime(y1, m1, d1)
                end_date = datetime(y2, m2, d2) + timedelta(days=1)
                date_label = f"{d1}-{m1}-{y1} ➜ {d2}-{m2}-{y2}"
            elif len(date_matches) == 1:
                d, m, y = map(int, date_matches[0])
                start_date = datetime(y, m, d)
                end_date = start_date + timedelta(days=1)
                date_label = f"{d}-{m}-{y}"
            else:
                raise ValueError("Format tanggal salah")

    except Exception:
        await ctx.send(
            "❌ Format tanggal salah!\n\n"
            "📌 Contoh penggunaan:\n"
            "`!intro_stats 19-10-2026 25-10-2026`\n"
            "`!intro_stats 19-10-2026`\n"
            "`!intro_stats` *(default 7 hari terakhir)*\n"
            "`!intro_stats tgl 19 bulan 10 tahun 2026 sampai tgl 25 bulan 10 tahun 2026`"
        )
        return

    await ctx.send("⏳ Menghitung data join, intro, dan aktivitas main-chat...")

    guild = ctx.guild

    joined_users = []
    for member in guild.members:
        if member.bot:
            continue
        if member.joined_at:
            joined_at = member.joined_at.replace(tzinfo=None)
            if start_date <= joined_at < end_date:
                joined_users.append(member)

    total_joined = len(joined_users)
    joined_user_ids = {m.id for m in joined_users}

    intro_channel = discord.utils.get(guild.text_channels, name="kenalan-dulu")
    if not intro_channel:
        intro_channel = discord.utils.find(lambda c: "kenalan" in c.name.lower(), guild.text_channels)

    main_chat = discord.utils.get(guild.text_channels, name="main-chat")
    if not main_chat:
        main_chat = discord.utils.find(
            lambda c: "main-chat" in c.name.lower() or "main_chat" in c.name.lower() or c.name.lower() == "mainchat",
            guild.text_channels
        )

    if total_joined == 0:
        result = (
            f"📋 **Intro & Activity Report — Kenalan Dulu & Main Chat**\n\n"
            f"📅 Periode: **{date_label}**\n"
            f"📍 Kenalan: {intro_channel.mention if intro_channel else '#kenalan-dulu'}\n"
            f"📍 Main Chat: {main_chat.mention if main_chat else '#main-chat'}\n\n"
            f"👥 **Join Activity**\n"
            f"➡️ Total User Baru Join: **0**\n\n"
            f"ℹ️ Tidak ada user baru yang bergabung pada periode ini."
        )
        progress_channel = discord.utils.get(guild.text_channels, name="progress")
        if progress_channel:
            await progress_channel.send(result)
            await ctx.send("✅ Intro stats berhasil dikirim ke #progress.")
        else:
            await ctx.send(result)
        return

    # 1. Scan kenalan-dulu (apakah sudah sapa/intro)
    intro_respondent_ids = set()
    if intro_channel:
        try:
            async for message in intro_channel.history(limit=None, after=start_date, before=end_date):
                if message.author.bot:
                    continue
                if message.created_at.replace(tzinfo=None) >= end_date:
                    break
                if message.author.id in joined_user_ids:
                    intro_respondent_ids.add(message.author.id)
        except Exception as e:
            print(f"❌ Error scan kenalan-dulu: {e}")

    # 2. Scan main-chat (hitung percakapan user baru)
    user_main_chat_counts = {uid: 0 for uid in joined_user_ids}
    total_main_chat_messages = 0

    if main_chat:
        try:
            async for message in main_chat.history(limit=None, after=start_date, before=end_date):
                if message.author.bot:
                    continue
                if message.created_at.replace(tzinfo=None) >= end_date:
                    break
                uid = message.author.id
                if uid in user_main_chat_counts:
                    user_main_chat_counts[uid] += 1
                    total_main_chat_messages += 1
        except Exception as e:
            print(f"❌ Error scan main-chat: {e}")

    # 3. Klasifikasi Intro Kenalan Dulu
    intro_respondents = [m for m in joined_users if m.id in intro_respondent_ids]
    no_intro = [m for m in joined_users if m.id not in intro_respondent_ids]
    total_intro = len(intro_respondents)
    total_no_intro = len(no_intro)
    intro_rate = round((total_intro / total_joined) * 100, 2)

    # 4. Klasifikasi Aktivitas Main Chat (Parameter aktif: percakapan > 1)
    active_members = []
    inactive_members = []

    for m in joined_users:
        msg_count = user_main_chat_counts.get(m.id, 0)
        if msg_count > 1:
            active_members.append((m, msg_count))
        else:
            inactive_members.append((m, msg_count))

    # Urutkan aktif dari pesan terbanyak
    active_members.sort(key=lambda x: (-x[1], x[0].display_name.lower()))
    # Urutkan belum aktif (yang punya 1 pesan di atas yang 0 pesan)
    inactive_members.sort(key=lambda x: (-x[1], x[0].display_name.lower()))

    total_active = len(active_members)
    total_inactive = len(inactive_members)
    active_rate = round((total_active / total_joined) * 100, 2)
    inactive_rate = round((total_inactive / total_joined) * 100, 2)

    count_1_msg = sum(1 for _, c in inactive_members if c == 1)
    count_0_msg = sum(1 for _, c in inactive_members if c == 0)

    # Preview max 15 nama
    active_preview_lines = [f"- {m.display_name} ({count} pesan)" for m, count in active_members[:15]]
    active_preview = "\n".join(active_preview_lines) if active_preview_lines else "-"
    if len(active_members) > 15:
        active_preview += f"\n... dan {len(active_members) - 15} user lainnya"

    inactive_preview_lines = [f"- {m.display_name} ({count} pesan)" for m, count in inactive_members[:15]]
    inactive_preview = "\n".join(inactive_preview_lines) if inactive_preview_lines else "-"
    if len(inactive_members) > 15:
        inactive_preview += f"\n... dan {len(inactive_members) - 15} user lainnya"

    result = (
        f"📋 **Intro & Activity Report — Kenalan Dulu & Main Chat**\n\n"
        f"📅 Periode: **{date_label}**\n"
        f"📍 Kenalan: {intro_channel.mention if intro_channel else '#kenalan-dulu'}\n"
        f"📍 Main Chat: {main_chat.mention if main_chat else '#main-chat'}\n\n"

        f"👥 **Join Activity**\n"
        f"➡️ Total User Baru Join: **{total_joined}**\n\n"

        f"🙋 **Kenalan Dulu (Intro)**\n"
        f"✅ Sudah Intro: **{total_intro}** ({intro_rate}%)\n"
        f"💤 Belum Intro: **{total_no_intro}**\n\n"

        f"💬 **Percakapan User Baru (Main Chat)**\n"
        f"📝 Total Pesan: **{total_main_chat_messages}**\n"
        f"🔥 **User Aktif (> 1 chat):** **{total_active}** ({active_rate}%)\n"
        f"💤 **User Belum Aktif (≤ 1 chat):** **{total_inactive}** ({inactive_rate}%)\n"
        f"*(Detail: {count_1_msg} user kirim 1 chat, {count_0_msg} user belum pernah chat)*\n\n"

        f"🔥 **User yang Sudah Aktif (> 1 chat):**\n"
        f"{active_preview}\n\n"

        f"💤 **User yang Belum Aktif (≤ 1 chat):**\n"
        f"{inactive_preview}"
    )

    progress_channel = discord.utils.get(guild.text_channels, name="progress")

    if progress_channel:
        await progress_channel.send(result)
        await ctx.send("✅ Intro stats berhasil dikirim ke #progress.")
    else:
        await ctx.send(result)