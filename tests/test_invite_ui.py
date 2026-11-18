import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord_bot.invite_ui import GenerateInviteView, ensure_generate_invite_panel, GENERATE_INVITE_CHANNEL
from config import ALGO_HC_ROLE, ALGO_HC_CATEGORY, ALGO_HC_DISCUSSION_CHANNEL, VERIFIED_ROLE


def test_ensure_generate_invite_panel_sends_when_not_exists():
    async def run():
        channel = MagicMock()
        guild = MagicMock()
        channel.guild = guild
        guild.me = MagicMock()

        async def empty_history(*args, **kwargs):
            if False:
                yield None

        channel.history = empty_history
        channel.send = AsyncMock()

        await ensure_generate_invite_panel(channel)

        channel.send.assert_awaited_once()
        assert channel.send.call_args[1]["embed"].title == "🎫 Generator Link Undangan Server"
        assert isinstance(channel.send.call_args[1]["view"], GenerateInviteView)

    asyncio.run(run())


def test_btn_generate_algo_hc_permission_denied():
    async def run():
        view = GenerateInviteView()
        interaction = MagicMock()
        interaction.user = MagicMock()
        interaction.user.guild_permissions.administrator = False
        interaction.user.guild_permissions.manage_guild = False
        interaction.user.roles = []
        interaction.response.send_message = AsyncMock()

        btn_algo_hc = view.children[0]
        await btn_algo_hc.callback(interaction)

        interaction.response.send_message.assert_awaited_once()
        assert "tidak memiliki izin" in interaction.response.send_message.call_args[0][0]

    asyncio.run(run())


def test_btn_generate_algo_hc_creates_invite():
    async def run():
        view = GenerateInviteView()
        interaction = MagicMock()
        member = MagicMock()
        member.guild_permissions.administrator = True
        interaction.user = member
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        hc_channel = MagicMock()
        hc_channel.name = "💬・discussion"
        hc_channel.category = MagicMock(name="Algo HC 2026")
        hc_channel.category.name = "Algo HC 2026"
        hc_channel.mention = "<#hc-channel-id>"

        fake_invite = MagicMock()
        fake_invite.url = "https://discord.gg/test-hc-123"
        fake_invite.code = "test-hc-123"
        hc_channel.create_invite = AsyncMock(return_value=fake_invite)

        guild = MagicMock()
        guild.text_channels = [hc_channel]
        interaction.guild = guild

        btn_algo_hc = view.children[0]

        with patch("discord_bot.events.cache_guild_invites", new_callable=AsyncMock):
            await btn_algo_hc.callback(interaction)

        hc_channel.create_invite.assert_awaited_once_with(
            max_age=0,
            max_uses=0,
            unique=True,
            reason=f"Generated via #{GENERATE_INVITE_CHANNEL} by {interaction.user}"
        )
        interaction.followup.send.assert_awaited_once()
        embed = interaction.followup.send.call_args[1]["embed"]
        assert "test-hc-123" in embed.description
        assert ALGO_HC_ROLE in embed.description

    asyncio.run(run())


def test_btn_generate_regular_creates_invite():
    async def run():
        view = GenerateInviteView()
        interaction = MagicMock()
        member = MagicMock()
        member.guild_permissions.administrator = True
        interaction.user = member
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        welcome_channel = MagicMock()
        welcome_channel.name = "kenalan-dulu"
        welcome_channel.mention = "<#welcome-id>"

        fake_invite = MagicMock()
        fake_invite.url = "https://discord.gg/regular-123"
        fake_invite.code = "regular-123"
        welcome_channel.create_invite = AsyncMock(return_value=fake_invite)

        guild = MagicMock()
        guild.text_channels = [welcome_channel]
        interaction.guild = guild

        btn_regular = view.children[1]

        with patch("discord_bot.events.cache_guild_invites", new_callable=AsyncMock):
            await btn_regular.callback(interaction)

        welcome_channel.create_invite.assert_awaited_once()
        interaction.followup.send.assert_awaited_once()
        embed = interaction.followup.send.call_args[1]["embed"]
        assert "regular-123" in embed.description
        assert VERIFIED_ROLE in embed.description

    asyncio.run(run())
