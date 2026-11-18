import discord # type: ignore
from discord.ui import View, Button # type: ignore
from config import (
    ALGO_HC_ROLE,
    ALGO_HC_CATEGORY,
    ALGO_HC_DISCUSSION_CHANNEL,
    VERIFIED_ROLE,
)

GENERATE_INVITE_CHANNEL = "generate-link-invitation"


class GenerateInviteView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Generate Link Algo HC 2026",
        style=discord.ButtonStyle.green,
        custom_id="btn_generate_algo_hc_invite",
        emoji="🟢"
    )
    async def btn_generate_algo_hc(self, interaction: discord.Interaction, button: Button):
        member = interaction.user
        has_perm = (
            getattr(member.guild_permissions, "administrator", False)
            or getattr(member.guild_permissions, "manage_guild", False)
            or any(role.name in ["Moderator", "Administrator", "Owner"] for role in getattr(member, "roles", []))
        )
        if not has_perm:
            await interaction.response.send_message(
                "❌ Kamu tidak memiliki izin untuk generate link invite server.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            await interaction.followup.send("❌ Error: Perintah harus dijalankan di server.", ephemeral=True)
            return

        # Cari channel landing Algo HC (prioritaskan #onboarding, fallback ke #discussion)
        hc_channel = discord.utils.find(
            lambda c: "onboarding" in c.name.lower()
            and getattr(getattr(c, "category", None), "name", "").lower() == ALGO_HC_CATEGORY.lower(),
            guild.text_channels
        )
        if not hc_channel:
            hc_channel = discord.utils.find(
                lambda c: ("discussion" in c.name.lower() or c.name == ALGO_HC_DISCUSSION_CHANNEL)
                and getattr(getattr(c, "category", None), "name", "").lower() == ALGO_HC_CATEGORY.lower(),
                guild.text_channels
            )
        if not hc_channel:
            hc_channel = discord.utils.find(
                lambda c: "onboarding" in c.name.lower() or "discussion" in c.name.lower() or c.name == ALGO_HC_DISCUSSION_CHANNEL,
                guild.text_channels
            )

        if not hc_channel:
            await interaction.followup.send(
                f"❌ Channel onboarding atau discussion untuk kategori `{ALGO_HC_CATEGORY}` tidak ditemukan. "
                f"Pastikan channel `#onboarding` sudah ada di server.",
                ephemeral=True
            )
            return

        try:
            invite = await hc_channel.create_invite(
                max_age=0,   # Tidak kedaluwarsa
                max_uses=0,  # Tanpa batas pemakaian
                unique=True,
                reason=f"Generated via #{GENERATE_INVITE_CHANNEL} by {interaction.user}"
            )

            from discord_bot.events import known_algo_hc_codes, cache_guild_invites
            known_algo_hc_codes.add(invite.code)
            await cache_guild_invites(guild)

            embed = discord.Embed(
                title="🟢 Link Invite Algo HC 2026 Berhasil Dibuat!",
                description=(
                    f"🔗 **Link Undangan:**\n`{invite.url}`\n\n"
                    f"📍 **Target Channel:** {hc_channel.mention}\n"
                    f"🏷️ **Auto Role:** `{ALGO_HC_ROLE}`\n\n"
                    f"📋 **Alur Bergabung Member Baru (Option B):**\n"
                    f"• Otomatis mendarat di {hc_channel.mention} dengan role `{ALGO_HC_ROLE}`.\n"
                    f"• Mengisi formulir onboarding (Parent / Student, alasan, lomba).\n"
                    f"• Setelah submit, mendapatkan role Parent/Student dan membuka akses ke channel diskusi & pengumuman!\n"
                    f"• **Tidak bisa melihat** channel reguler lainnya.\n\n"
                    f"*(Link ini permanen dan dapat langsung dibagikan ke siswa/parent Algo HC)*"
                ),
                color=0x2ecc71
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Gagal membuat link invite Algo HC: {e}", ephemeral=True)

    @discord.ui.button(
        label="Generate Link Siswa Reguler",
        style=discord.ButtonStyle.blurple,
        custom_id="btn_generate_regular_invite",
        emoji="🔵"
    )
    async def btn_generate_regular(self, interaction: discord.Interaction, button: Button):
        member = interaction.user
        has_perm = (
            getattr(member.guild_permissions, "administrator", False)
            or getattr(member.guild_permissions, "manage_guild", False)
            or any(role.name in ["Moderator", "Administrator", "Owner"] for role in getattr(member, "roles", []))
        )
        if not has_perm:
            await interaction.response.send_message(
                "❌ Kamu tidak memiliki izin untuk generate link invite server.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            await interaction.followup.send("❌ Error: Perintah harus dijalankan di server.", ephemeral=True)
            return

        landing_channel = discord.utils.find(
            lambda c: "kenalan" in c.name.lower() or "welcome" in c.name.lower() or "rules" in c.name.lower(),
            guild.text_channels
        )
        if not landing_channel and guild.text_channels:
            landing_channel = guild.text_channels[0]

        if not landing_channel:
            await interaction.followup.send("❌ Channel tujuan landing tidak ditemukan.", ephemeral=True)
            return

        try:
            invite = await landing_channel.create_invite(
                max_age=0,
                max_uses=0,
                unique=True,
                reason=f"Regular Student invite generated by {interaction.user}"
            )

            from discord_bot.events import cache_guild_invites
            await cache_guild_invites(guild)

            embed = discord.Embed(
                title="🔵 Link Invite Siswa Reguler Berhasil Dibuat!",
                description=(
                    f"🔗 **Link Undangan:**\n`{invite.url}`\n\n"
                    f"📍 **Target Channel:** {landing_channel.mention}\n"
                    f"🏷️ **Auto Role:** `{VERIFIED_ROLE}`\n\n"
                    f"📋 **Hak Akses Member Baru:**\n"
                    f"• Otomatis mendapatkan role `{VERIFIED_ROLE}`.\n"
                    f"• Dapat mengakses seluruh channel komunitas & materi reguler."
                ),
                color=0x3498db
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Gagal membuat link invite reguler: {e}", ephemeral=True)


async def ensure_generate_invite_panel(channel):
    try:
        async for message in channel.history(limit=20):
            if message.author.id == channel.guild.me.id and message.embeds:
                if message.embeds[0].title == "🎫 Generator Link Undangan Server":
                    print(f"ℹ️ Panel invite sudah ada di #{channel.name}")
                    return

        embed = discord.Embed(
            title="🎫 Generator Link Undangan Server",
            description=(
                "Gunakan tombol di bawah untuk membuat link undangan server secara instan:\n\n"
                "🟢 **Link Khusus Algo HC 2026**:\n"
                "• Khusus siswa program Algo HC 2026.\n"
                "• Otomatis mendapatkan role `Algo HC 2026`.\n"
                "• **Hanya bisa melihat 2 channel** di kategori `Algo HC 2026`.\n\n"
                "🔵 **Link Siswa Reguler (Umum)**:\n"
                "• Khusus siswa reguler Algorithmics/Algonova.\n"
                "• Otomatis mendapatkan role `🏅 | Verified Student`.\n"
                "• Mendapatkan akses ke seluruh channel komunitas.\n\n"
                "🔒 *Link yang dibuat bersifat privat (hanya terlihat oleh Anda).* "
            ),
            color=0x2b2d31
        )

        await channel.send(embed=embed, view=GenerateInviteView())
        print(f"✅ Berhasil mengirim panel generator invite ke #{channel.name}")
    except Exception as e:
        print(f"❌ Gagal mengirim panel generator invite ke #{channel.name}: {e}")

