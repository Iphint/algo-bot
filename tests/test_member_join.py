import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from config import VERIFIED_ROLE, ALGO_HC_ROLE
from discord_bot.events import on_member_join, guild_invites, known_algo_hc_codes, is_algo_hc_invite


def test_on_member_join_assigns_verified_student_by_default():
    verified_role = MagicMock()
    verified_role.name = VERIFIED_ROLE

    hc_role = MagicMock()
    hc_role.name = ALGO_HC_ROLE

    guild = MagicMock()
    guild.id = 1001
    guild.roles = [verified_role, hc_role]
    guild.name = "Test Guild"
    guild.text_channels = []
    guild.me = MagicMock()
    guild.me.guild_permissions.manage_guild = False

    member = MagicMock()
    member.guild = guild
    member.bot = False
    member.id = 12345678
    member.name = "TestStudent"
    member.add_roles = AsyncMock()

    with patch("discord_bot.events.notify_moderators_new_member", new_callable=AsyncMock):
        asyncio.run(on_member_join(member))

    member.add_roles.assert_awaited_once_with(verified_role, reason="Auto assign Verified Student role on join")


def test_on_member_join_assigns_algo_hc_via_hc_invite():
    verified_role = MagicMock()
    verified_role.name = VERIFIED_ROLE

    hc_role = MagicMock()
    hc_role.name = ALGO_HC_ROLE

    # Setup channels
    hc_discussion = MagicMock()
    hc_discussion.name = "💬・discussion"
    hc_discussion.category = MagicMock(name="Algo HC 2026")
    hc_discussion.category.name = "Algo HC 2026"
    hc_discussion.send = AsyncMock()

    guild = MagicMock()
    guild.id = 1002
    guild.roles = [verified_role, hc_role]
    guild.name = "Test Guild"
    guild.text_channels = [hc_discussion]
    guild.me = MagicMock()
    guild.me.guild_permissions.manage_guild = True

    # Setup invite tracking
    # Old cache had uses = 0
    guild_invites[guild.id] = {
        "hc_code_123": {
            "uses": 0,
            "channel_id": 999,
            "channel_name": "💬・discussion",
            "category_name": "Algo HC 2026"
        }
    }

    # New invite has uses = 1
    new_invite = MagicMock()
    new_invite.code = "hc_code_123"
    new_invite.uses = 1
    new_invite.channel = hc_discussion
    guild.invites = AsyncMock(return_value=[new_invite])

    member = MagicMock()
    member.guild = guild
    member.bot = False
    member.id = 55667788
    member.name = "AlgoHCStudent"
    member.mention = "<@55667788>"
    member.add_roles = AsyncMock()

    with patch("discord_bot.events.notify_moderators_new_member", new_callable=AsyncMock) as mock_notify:
        asyncio.run(on_member_join(member))

    # Verify Algo HC role was given and NOT verified_role
    member.add_roles.assert_awaited_once_with(hc_role, reason="Auto assign Algo HC 2026 role via Algo HC invite")
    # Verify welcome was sent to discussion channel
    hc_discussion.send.assert_awaited_once()
    assert "Algo HC 2026" in hc_discussion.send.call_args[0][0]
    # Verify moderator notified with is_algo_hc=True
    mock_notify.assert_awaited_once_with(member, is_algo_hc=True)


def test_on_member_join_skips_bot():
    role = MagicMock()
    role.name = VERIFIED_ROLE

    guild = MagicMock()
    guild.roles = [role]
    guild.name = "Test Guild"
    guild.text_channels = []
    guild.me = MagicMock()
    guild.me.guild_permissions.manage_guild = False

    member = MagicMock()
    member.guild = guild
    member.bot = True
    member.id = 99999999
    member.name = "TestBot"
    member.add_roles = AsyncMock()

    with patch("discord_bot.events.notify_moderators_new_member", new_callable=AsyncMock):
        asyncio.run(on_member_join(member))

    member.add_roles.assert_not_called()


def test_is_algo_hc_invite_detection():
    # Detect by category name
    assert is_algo_hc_invite("any_code", "general", "Algo HC 2026") is True
    # Detect by channel name
    assert is_algo_hc_invite("any_code", "💬・discussion", "Algo HC 2026") is True
    assert is_algo_hc_invite("any_code", "📢・announcements", "Algo HC 2026") is True
    # Registered code
    known_algo_hc_codes.add("custom_hc_invite")
    assert is_algo_hc_invite("custom_hc_invite", "random_channel", "Random Cat") is True
    # Regular invite
    assert is_algo_hc_invite("random_code", "welcome", "General") is False


def test_auto_lock_algohc_command():
    from discord_bot.commands import auto_lock_algohc

    algo_role = MagicMock()
    algo_role.name = ALGO_HC_ROLE

    hc_category = MagicMock()
    hc_category.name = "Algo HC 2026"
    hc_category.set_permissions = AsyncMock()

    regular_category = MagicMock()
    regular_category.name = "Public Chat"
    regular_category.set_permissions = AsyncMock()
    regular_category.channels = []

    guild = MagicMock()
    guild.roles = [algo_role]
    guild.categories = [hc_category, regular_category]
    guild.text_channels = []

    ctx = MagicMock()
    ctx.guild = guild
    ctx.send = AsyncMock()

    asyncio.run(auto_lock_algohc._callback(ctx))

    hc_category.set_permissions.assert_awaited_once_with(algo_role, view_channel=True, send_messages=True)
    regular_category.set_permissions.assert_awaited_once_with(algo_role, view_channel=False)
