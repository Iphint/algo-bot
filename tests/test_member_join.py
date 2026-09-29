import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from config import VERIFIED_ROLE
from discord_bot.events import on_member_join


def test_on_member_join_assigns_role():
    role = MagicMock()
    role.name = VERIFIED_ROLE

    guild = MagicMock()
    guild.roles = [role]
    guild.name = "Test Guild"
    guild.text_channels = []

    member = MagicMock()
    member.guild = guild
    member.bot = False
    member.id = 12345678
    member.name = "TestStudent"
    member.add_roles = AsyncMock()

    with patch("discord_bot.events.notify_moderators_new_member", new_callable=AsyncMock):
        asyncio.run(on_member_join(member))

    member.add_roles.assert_awaited_once_with(role, reason="Auto assign Verified Student role on join")


def test_on_member_join_skips_bot():
    role = MagicMock()
    role.name = VERIFIED_ROLE

    guild = MagicMock()
    guild.roles = [role]
    guild.name = "Test Guild"
    guild.text_channels = []

    member = MagicMock()
    member.guild = guild
    member.bot = True
    member.id = 99999999
    member.name = "TestBot"
    member.add_roles = AsyncMock()

    with patch("discord_bot.events.notify_moderators_new_member", new_callable=AsyncMock):
        asyncio.run(on_member_join(member))

    member.add_roles.assert_not_called()
