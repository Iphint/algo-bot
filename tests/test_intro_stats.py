import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord_bot.templates import get_intro_message, get_random_intro
from discord_bot.events import pending_intro, on_message
from discord_bot.commands import intro_stats


def test_intro_template_invites_to_main_chat():
    class DummyChannel:
        name = "main-chat"
        mention = "<#123456789>"

    class DummyGuild:
        text_channels = [DummyChannel()]

    class DummyMember:
        name = "SiswaBaru"
        mention = "<@111222333>"
        guild = DummyGuild()

    msg = get_intro_message([DummyMember()])
    assert "<@111222333>" in msg
    assert "<#123456789>" in msg
    # Verify no obsolete verification rules text
    assert "#📜︱rules" not in msg
    assert "centang ✅" not in msg


def test_multi_intro_template_invites_to_main_chat():
    class DummyChannel:
        name = "main-chat"
        mention = "<#123456789>"

    class DummyGuild:
        text_channels = [DummyChannel()]

    class DummyMember:
        def __init__(self, name, uid):
            self.name = name
            self.mention = f"<@{uid}>"
            self.guild = DummyGuild()

    m1 = DummyMember("Siswa1", 101)
    m2 = DummyMember("Siswa2", 102)

    msg = get_intro_message([m1, m2])
    assert "<@101>" in msg
    assert "<@102>" in msg
    assert "<#123456789>" in msg
    assert "#📜︱rules" not in msg


def test_on_message_tracks_main_chat_for_pending_intro():
    user_id = 998877
    pending_intro[user_id] = {
        "time": datetime.utcnow(),
        "replied": False
    }

    class DummyChannel:
        name = "main-chat"

    class DummyAuthor:
        id = user_id
        name = "ActiveUser"
        bot = False
        roles = []

    class DummyGuild:
        roles = []

    message = MagicMock()
    message.author = DummyAuthor()
    message.channel = DummyChannel()
    message.guild = DummyGuild()
    message.content = "Halo semua!"

    with patch("discord_bot.events.handle_profanity_filter", new_callable=AsyncMock), \
         patch("discord_bot.events.handle_spam_filter", new_callable=AsyncMock), \
         patch("discord_bot.events.bot.process_commands", new_callable=AsyncMock):
        asyncio.run(on_message(message))

    assert pending_intro[user_id]["replied"] is True


def test_intro_stats_active_vs_inactive_logic():
    # Setup test members:
    # m1: 3 messages in main-chat (>1 -> AKTIF)
    # m2: 1 message in main-chat (<=1 -> BELUM AKTIF)
    # m3: 0 messages in main-chat (<=1 -> BELUM AKTIF)
    class DummyMember:
        def __init__(self, uid, name, joined_at):
            self.id = uid
            self.name = name
            self.display_name = name
            self.bot = False
            self.joined_at = joined_at

    m1 = DummyMember(1, "User1", datetime(2026, 10, 20))
    m2 = DummyMember(2, "User2", datetime(2026, 10, 21))
    m3 = DummyMember(3, "User3", datetime(2026, 10, 22))

    class DummyMessage:
        def __init__(self, uid, created_at):
            self.author = MagicMock(id=uid, bot=False)
            self.created_at = created_at

    # Messages in main-chat
    mc_messages = [
        DummyMessage(1, datetime(2026, 10, 20, 10, 0)),
        DummyMessage(1, datetime(2026, 10, 20, 11, 0)),
        DummyMessage(1, datetime(2026, 10, 20, 12, 0)),
        DummyMessage(2, datetime(2026, 10, 21, 10, 0)),
    ]

    async def fake_mc_history(*args, **kwargs):
        for msg in mc_messages:
            yield msg

    class DummyMainChat:
        name = "main-chat"
        mention = "<#main-chat>"
        history = fake_mc_history

    class DummyIntroChannel:
        name = "kenalan-dulu"
        mention = "<#kenalan-dulu>"

        async def history(self, *args, **kwargs):
            yield DummyMessage(1, datetime(2026, 10, 20, 9, 0))

    class DummyProgressChannel:
        name = "progress"
        send = AsyncMock()

    class DummyGuild:
        members = [m1, m2, m3]
        text_channels = [DummyMainChat(), DummyIntroChannel(), DummyProgressChannel()]

    ctx = MagicMock()
    ctx.guild = DummyGuild()
    ctx.send = AsyncMock()

    # Run intro_stats with date arguments
    asyncio.run(intro_stats._callback(ctx, "19-10-2026", "25-10-2026"))

    # Assert progress channel received message
    DummyProgressChannel.send.assert_awaited_once()
    result_text = DummyProgressChannel.send.call_args[0][0]

    # Verify content in report:
    assert "Total User Baru Join: **3**" in result_text
    assert "User Aktif (> 1 chat):** **1**" in result_text
    assert "User Belum Aktif (≤ 1 chat):** **2**" in result_text
    assert "User1 (3 pesan)" in result_text
    assert "User2 (1 pesan)" in result_text
    assert "User3 (0 pesan)" in result_text
