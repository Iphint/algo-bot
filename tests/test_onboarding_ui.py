import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from config import (
    ALGO_HC_ROLE,
    ROLE_PARENT,
    ROLE_STUDENT,
    ALGO_HC_CATEGORY,
    ALGO_HC_DISCUSSION_CHANNEL,
    ALGO_HC_ANNOUNCEMENT_CHANNEL,
    ALGO_HC_ONBOARDING_CHANNEL,
)
from discord_bot.onboarding_ui import (
    find_role_resilient,
    get_or_create_role,
    AlgoHCOnboardingLaunchView,
    AlgoHCOnboardingWizardView,
    AlgoHCOnboardingModal,
    CustomReasonModal,
    ensure_onboarding_panel,
)


def test_find_role_resilient():
    guild = MagicMock()
    parent_role = MagicMock()
    parent_role.name = ROLE_PARENT

    student_role = MagicMock()
    student_role.name = ROLE_STUDENT

    hc_role = MagicMock()
    hc_role.name = ALGO_HC_ROLE

    guild.roles = [parent_role, student_role, hc_role]

    # Exact matches
    assert find_role_resilient(guild, ROLE_PARENT) == parent_role
    assert find_role_resilient(guild, ROLE_STUDENT) == student_role
    assert find_role_resilient(guild, ALGO_HC_ROLE) == hc_role

    # Fuzzy matches
    assert find_role_resilient(guild, "parent") == parent_role
    assert find_role_resilient(guild, "student") == student_role
    assert find_role_resilient(guild, "algo") == hc_role


def test_get_or_create_role_creates_when_missing():
    guild = MagicMock()
    guild.roles = []
    created_role = MagicMock()
    created_role.name = ROLE_PARENT
    guild.create_role = AsyncMock(return_value=created_role)

    role = asyncio.run(get_or_create_role(guild, ROLE_PARENT, "parent"))
    assert role == created_role
    guild.create_role.assert_awaited_once()


def test_wizard_state_and_button_styles():
    async def run_test():
        wizard = AlgoHCOnboardingWizardView(user_id=123)
        assert wizard.role_type is None
        assert wizard.reason is None
        assert wizard.is_competition is None
        assert wizard.btn_submit.disabled is True

        # Click Parent
        interaction = MagicMock()
        interaction.user.id = 123
        interaction.response.edit_message = AsyncMock()

        await wizard.btn_parent.callback(interaction)
        assert wizard.role_type == "parent"
        assert wizard.btn_parent.style == discord.ButtonStyle.primary
        assert wizard.btn_student.style == discord.ButtonStyle.secondary
        assert wizard.btn_submit.disabled is True  # still missing reason & competition

        # Select Reason
        wizard.select_reason._values = ["lomba_coding"]
        await wizard.select_reason.callback(interaction)
        assert "Persiapan Lomba" in wizard.reason
        assert wizard.btn_submit.disabled is True  # still missing competition

        # Click Yes for competition
        await wizard.btn_comp_yes.callback(interaction)
        assert wizard.is_competition == "yes"
        assert wizard.btn_comp_yes.style == discord.ButtonStyle.success
        assert wizard.btn_submit.disabled is False  # all filled!

        embed = wizard.build_embed()
        assert ROLE_PARENT in embed.description
        assert "Lomba" in embed.description

    asyncio.run(run_test())


def test_wizard_custom_reason_modal():
    async def run_test():
        wizard = AlgoHCOnboardingWizardView(user_id=123)
        modal = CustomReasonModal(wizard_view=wizard)
        modal.custom_input._value = "Ingin ikut seleksi olimpiade"

        interaction = MagicMock()
        interaction.response.edit_message = AsyncMock()

        await modal.on_submit(interaction)
        assert "Ingin ikut seleksi olimpiade" in wizard.reason
        assert wizard.reason.startswith("✍️")

    asyncio.run(run_test())


def test_wizard_submit_assigns_parent_role():
    async def run_test():
        wizard = AlgoHCOnboardingWizardView(user_id=456)
        wizard.role_type = "parent"
        wizard.reason = "🏆 Persiapan Lomba Coding"
        wizard.is_competition = "yes"
        wizard.sync_button_styles()

        parent_role = MagicMock()
        parent_role.name = ROLE_PARENT

        student_role = MagicMock()
        student_role.name = ROLE_STUDENT

        algo_role = MagicMock()
        algo_role.name = ALGO_HC_ROLE

        discussion_ch = MagicMock()
        discussion_ch.name = "discussion"
        discussion_ch.category = MagicMock()
        discussion_ch.category.name = "Algo HC 2026"
        discussion_ch.send = AsyncMock()

        log_ch = MagicMock()
        log_ch.name = "member-log"
        log_ch.send = AsyncMock()

        guild = MagicMock()
        guild.name = "Algo Server"
        guild.roles = [parent_role, student_role, algo_role]
        guild.text_channels = [discussion_ch, log_ch]

        member = MagicMock(spec=discord.Member)
        member.id = 456
        member.name = "TestParent"
        member.mention = "<@456>"
        member.roles = [algo_role, student_role]  # currently has old student role
        member.add_roles = AsyncMock()
        member.remove_roles = AsyncMock()
        member.display_avatar = None

        interaction = MagicMock()
        interaction.user = member
        interaction.guild = guild
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        await wizard.btn_submit.callback(interaction)

        # Parent role added
        member.add_roles.assert_awaited_once_with(parent_role, reason="Algo HC Onboarding completed")
        # Old Student role removed
        member.remove_roles.assert_awaited_once_with(student_role, reason="Algo HC Onboarding status switch")
        # Log sent
        log_ch.send.assert_awaited_once()
        # Welcome sent in discussion
        discussion_ch.send.assert_awaited_once()
        assert "Parent" in discussion_ch.send.call_args[0][0]
        # Success message to user
        interaction.followup.send.assert_awaited_once()

    asyncio.run(run_test())


def test_wizard_submit_assigns_student_role():
    async def run_test():
        wizard = AlgoHCOnboardingWizardView(user_id=789)
        wizard.role_type = "student"
        wizard.reason = "💡 Mengasah Logika"
        wizard.is_competition = "no"
        wizard.sync_button_styles()

        parent_role = MagicMock()
        parent_role.name = ROLE_PARENT

        student_role = MagicMock()
        student_role.name = ROLE_STUDENT

        algo_role = MagicMock()
        algo_role.name = ALGO_HC_ROLE

        discussion_ch = MagicMock()
        discussion_ch.name = "discussion"
        discussion_ch.category = MagicMock()
        discussion_ch.category.name = "Algo HC 2026"
        discussion_ch.send = AsyncMock()

        guild = MagicMock()
        guild.name = "Algo Server"
        guild.roles = [parent_role, student_role, algo_role]
        guild.text_channels = [discussion_ch]

        member = MagicMock(spec=discord.Member)
        member.id = 789
        member.name = "TestStudent"
        member.mention = "<@789>"
        member.roles = []  # no roles yet
        member.add_roles = AsyncMock()
        member.remove_roles = AsyncMock()
        member.display_avatar = None

        interaction = MagicMock()
        interaction.user = member
        interaction.guild = guild
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        await wizard.btn_submit.callback(interaction)

        # Both algo_role and student_role added
        member.add_roles.assert_awaited_once_with(algo_role, student_role, reason="Algo HC Onboarding completed")
        # Welcome sent in discussion
        discussion_ch.send.assert_awaited_once()
        assert "Student" in discussion_ch.send.call_args[0][0]

    asyncio.run(run_test())


def test_ensure_onboarding_panel_sends_when_empty():
    async def run_test():
        channel = MagicMock()
        channel.name = "onboarding"
        channel.guild.me = MagicMock()

        async def empty_history(limit=20):
            if False:
                yield None

        channel.history = empty_history
        channel.send = AsyncMock()

        await ensure_onboarding_panel(channel)
        channel.send.assert_awaited_once()
        call_kwargs = channel.send.call_args[1]
        assert "embed" in call_kwargs
        assert isinstance(call_kwargs["view"], AlgoHCOnboardingLaunchView)

    asyncio.run(run_test())


def test_ensure_onboarding_panel_skips_when_exists():
    async def run_test():
        channel = MagicMock()
        channel.name = "onboarding"
        bot_user = MagicMock()
        channel.guild.me = bot_user

        existing_msg = MagicMock()
        existing_msg.author = bot_user
        existing_embed = MagicMock()
        existing_embed.title = "📋 Onboarding Algo HC 2026"
        existing_msg.embeds = [existing_embed]

        async def existing_history(limit=20):
            yield existing_msg

        channel.history = existing_history
        channel.send = AsyncMock()

        await ensure_onboarding_panel(channel)
        channel.send.assert_not_called()

    asyncio.run(run_test())


def test_launch_view_sends_wizard():
    async def run_test():
        launch_view = AlgoHCOnboardingLaunchView()
        interaction = MagicMock()
        interaction.user.id = 123
        interaction.response.send_message = AsyncMock()

        await launch_view.btn_launch_onboarding.callback(interaction)
        interaction.response.send_message.assert_awaited_once()
        call_kwargs = interaction.response.send_message.call_args[1]
        assert "embed" in call_kwargs
        assert isinstance(call_kwargs["view"], AlgoHCOnboardingWizardView)
        assert call_kwargs["ephemeral"] is True

    asyncio.run(run_test())


def test_popup_modal_submit_assigns_parent():
    async def run_test():
        modal = AlgoHCOnboardingModal()
        modal.status_input._value = "Parent"
        modal.reason_input._value = "Mendukung anak belajar programming"
        modal.comp_input._value = "Ya"

        parent_role = MagicMock()
        parent_role.name = ROLE_PARENT

        algo_role = MagicMock()
        algo_role.name = ALGO_HC_ROLE

        discussion_ch = MagicMock()
        discussion_ch.name = "discussion"
        discussion_ch.category = MagicMock()
        discussion_ch.category.name = "Algo HC 2026"
        discussion_ch.send = AsyncMock()

        log_ch = MagicMock()
        log_ch.name = "member-log"
        log_ch.send = AsyncMock()

        guild = MagicMock()
        guild.name = "Algo Server"
        guild.roles = [parent_role, algo_role]
        guild.text_channels = [discussion_ch, log_ch]

        member = MagicMock(spec=discord.Member)
        member.id = 111
        member.name = "ParentUser"
        member.mention = "<@111>"
        member.roles = []
        member.add_roles = AsyncMock()
        member.remove_roles = AsyncMock()
        member.display_avatar = None

        interaction = MagicMock()
        interaction.user = member
        interaction.guild = guild
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        await modal.on_submit(interaction)

        member.add_roles.assert_awaited_once_with(algo_role, parent_role, reason="Algo HC Onboarding pop-up completed")
        log_ch.send.assert_awaited_once()
        discussion_ch.send.assert_awaited_once()
        assert "Parent" in discussion_ch.send.call_args[0][0]
        interaction.followup.send.assert_awaited_once()

    asyncio.run(run_test())


def test_popup_modal_submit_invalid_status():
    async def run_test():
        modal = AlgoHCOnboardingModal()
        modal.status_input._value = "Tamu biasa"
        modal.reason_input._value = "Hanya coba-coba"
        modal.comp_input._value = "Tidak"

        guild = MagicMock()
        guild.roles = []
        guild.text_channels = []

        member = MagicMock(spec=discord.Member)
        member.id = 222
        member.name = "UnknownUser"
        member.roles = []
        member.add_roles = AsyncMock()

        interaction = MagicMock()
        interaction.user = member
        interaction.guild = guild
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        await modal.on_submit(interaction)

        # No roles added
        member.add_roles.assert_not_called()
        # Warning sent to user
        interaction.followup.send.assert_awaited_once()
        assert "tidak dapat dikenali" in interaction.followup.send.call_args[0][0]

    asyncio.run(run_test())
