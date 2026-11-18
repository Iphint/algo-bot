import discord # type: ignore
from discord.ui import View, Button, Select, Modal, TextInput, button, select # type: ignore
from typing import Optional
from config import (
    ALGO_HC_ROLE,
    ALGO_HC_CATEGORY,
    ALGO_HC_DISCUSSION_CHANNEL,
    ALGO_HC_ANNOUNCEMENT_CHANNEL,
    ALGO_HC_ONBOARDING_CHANNEL,
    ROLE_PARENT,
    ROLE_STUDENT,
    VERIFIED_ROLE,
)

REASON_MAP = {
    "lomba_coding": "🏆 Persiapan Lomba Coding / Olimpiade",
    "asah_logika": "💡 Mengasah Logika & Pemrograman",
    "rekomendasi_sekolah": "🏫 Rekomendasi dari Guru / Sekolah",
    "info_algo": "📢 Info Seputar Algo Hackathon",
}


def find_role_resilient(guild, role_name_or_keyword: str) -> Optional[discord.Role]:
    """Cari role secara tepat atau toleran (fuzzy) berdasarkan nama/kata kunci."""
    if not guild or not hasattr(guild, "roles"):
        return None

    # 1. Exact match
    role = discord.utils.get(guild.roles, name=role_name_or_keyword)
    if role:
        return role

    # 2. Fuzzy match
    kw = role_name_or_keyword.lower()
    if "parent" in kw:
        return discord.utils.find(lambda r: "parent" in r.name.lower(), guild.roles)
    if "student" in kw:
        return discord.utils.find(
            lambda r: "student" in r.name.lower()
            and "verified" not in r.name.lower()
            and "python" not in r.name.lower(),
            guild.roles
        )
    if "algo" in kw or "hc" in kw:
        return discord.utils.find(
            lambda r: "algo" in r.name.lower() and "hc" in r.name.lower(),
            guild.roles
        )
    return None


async def get_or_create_role(guild, role_name: str, fallback_kw: str = "") -> Optional[discord.Role]:
    """Cari role, dan jika belum ada, buatkan otomatis di guild."""
    role = find_role_resilient(guild, role_name)
    if not role and fallback_kw:
        role = find_role_resilient(guild, fallback_kw)

    if not role:
        try:
            role = await guild.create_role(
                name=role_name,
                reason="Auto-create role for Algo HC 2026 onboarding"
            )
            print(f"✅ Otomatis membuat role baru: '{role_name}' di guild '{guild.name}'")
        except Exception as e:
            print(f"⚠️ Gagal membuat role '{role_name}': {e}")
    return role


async def send_onboarding_log(guild: discord.Guild, member: discord.Member, role_type: str, reason: str, is_competition: str):
    log_channel = discord.utils.find(
        lambda c: "member-log" in c.name.lower() or "join-leave-log" in c.name.lower() or "log" in c.name.lower(),
        guild.text_channels
    )
    if not log_channel:
        return

    status_label = "👨‍👩‍👧 Parent" if role_type == "parent" else "🎓 Student"
    comp_label = "✅ Ya, Ikut Lomba" if is_competition == "yes" else "❌ Tidak / Belum"

    embed = discord.Embed(
        title="📋 Onboarding Selesai: Algo HC 2026",
        color=0x2ecc71
    )
    embed.add_field(name="Member", value=f"{member.mention} (`{member}` | ID: `{member.id}`)", inline=False)
    embed.add_field(name="Status", value=status_label, inline=True)
    embed.add_field(name="Ikut Lomba?", value=comp_label, inline=True)
    embed.add_field(name="Alasan Join", value=reason or "-", inline=False)
    embed.set_thumbnail(url=member.display_avatar.url if member.display_avatar else None)
    embed.timestamp = discord.utils.utcnow()

    try:
        await log_channel.send(embed=embed)
    except Exception as e:
        print(f"⚠️ Gagal kirim log onboarding ke #{log_channel.name}: {e}")


async def send_welcome_in_discussion(guild: discord.Guild, member: discord.Member, role_label: str):
    discussion_channel = discord.utils.find(
        lambda c: ("discussion" in c.name.lower() or c.name == ALGO_HC_DISCUSSION_CHANNEL)
        and getattr(getattr(c, "category", None), "name", "").lower() == ALGO_HC_CATEGORY.lower(),
        guild.text_channels
    )
    if not discussion_channel:
        discussion_channel = discord.utils.find(
            lambda c: "discussion" in c.name.lower() or c.name == ALGO_HC_DISCUSSION_CHANNEL,
            guild.text_channels
        )

    if not discussion_channel:
        return

    welcome_text = (
        f"Halo {member.mention}! 👋 Selamat datang di **Algo HC 2026** sebagai **{role_label}**! "
        f"Yuk langsung sapa teman-teman dan mulai diskusi santai di sini yaa 😄🚀"
    )
    try:
        await discussion_channel.send(welcome_text)
    except Exception as e:
        print(f"⚠️ Gagal kirim welcome di discussion channel: {e}")


class AlgoHCOnboardingModal(Modal, title="📋 Onboarding Algo HC 2026"):
    """Pop-up modal formulir onboarding Algo HC."""
    status_input = TextInput(
        label="1. Status (Parent / Student)",
        placeholder="Ketik: Parent atau Student",
        required=True,
        max_length=25,
        style=discord.TextStyle.short
    )

    reason_input = TextInput(
        label="2. Alasan Bergabung",
        placeholder="Contoh: Mengasah logika coding, persiapan lomba...",
        required=True,
        max_length=200,
        style=discord.TextStyle.paragraph
    )

    comp_input = TextInput(
        label="3. Ikut Lomba Algo? (Ya / Tidak)",
        placeholder="Ketik: Ya atau Tidak",
        required=True,
        max_length=15,
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        member = interaction.user

        if not guild or not isinstance(member, discord.Member):
            await interaction.followup.send("❌ Error: Interaksi harus dilakukan di dalam server.", ephemeral=True)
            return

        raw_status = self.status_input.value.strip().lower()
        if any(w in raw_status for w in ["parent", "orang tua", "ortu", "ayah", "ibu", "bunda", "mama", "papa"]) or raw_status == "p":
            role_type = "parent"
            target_role_name = ROLE_PARENT
            opposite_role_name = ROLE_STUDENT
        elif any(w in raw_status for w in ["student", "siswa", "murid", "anak", "pelajar", "peserta"]) or raw_status == "s":
            role_type = "student"
            target_role_name = ROLE_STUDENT
            opposite_role_name = ROLE_PARENT
        else:
            await interaction.followup.send(
                "⚠️ Status tidak dapat dikenali. Harap ketik **Parent** atau **Student** pada pertanyaan nomor 1.",
                ephemeral=True
            )
            return

        raw_comp = self.comp_input.value.strip().lower()
        if any(w in raw_comp for w in ["ya", "yes", "y", "ikut", "mau", "benar", "tentu"]):
            is_competition = "yes"
        else:
            is_competition = "no"

        reason = self.reason_input.value.strip()

        # Update role
        algo_role = await get_or_create_role(guild, ALGO_HC_ROLE, "algo")
        target_role = await get_or_create_role(guild, target_role_name, role_type)
        opposite_role = find_role_resilient(guild, opposite_role_name)

        roles_to_add = []
        if algo_role and algo_role not in member.roles:
            roles_to_add.append(algo_role)
        if target_role and target_role not in member.roles:
            roles_to_add.append(target_role)

        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason="Algo HC Onboarding pop-up completed")
            except Exception as e:
                print(f"❌ Gagal memberikan role ke {member.name}: {e}")

        if opposite_role and opposite_role in member.roles:
            try:
                await member.remove_roles(opposite_role, reason="Algo HC Onboarding status switch")
            except Exception as e:
                print(f"⚠️ Gagal menghapus role lama {opposite_role.name}: {e}")

        # Log & welcome
        await send_onboarding_log(guild, member, role_type, reason, is_competition)
        await send_welcome_in_discussion(guild, member, target_role_name)

        # Success message to user
        success_embed = discord.Embed(
            title="🎉 Onboarding Algo HC Berhasil!",
            description=(
                f"Terima kasih telah mengisi formulir onboarding, {member.mention}!\n\n"
                f"🏷️ **Role Anda:** `{target_role_name}` & `{ALGO_HC_ROLE}`\n"
                f"🔓 **Akses Terbuka:** Channel diskusi (**#discussion**) dan pengumuman (**#announcement**) "
                f"kini sudah dapat Anda akses!\n\n"
                f"Silakan langsung menuju channel **#discussion** untuk menyapa teman-teman lainnya ya! 🚀"
            ),
            color=0x2ecc71
        )
        await interaction.followup.send(embed=success_embed, ephemeral=True)


class CustomReasonModal(Modal):
    """Modal untuk memasukkan alasan bergabung custom jika memilih 'Lainnya / Other'."""
    def __init__(self, wizard_view: "AlgoHCOnboardingWizardView"):
        super().__init__(title="Tuliskan Alasan Bergabung")
        self.wizard_view = wizard_view
        self.custom_input = TextInput(
            label="Alasan Bergabung",
            placeholder="Contoh: Ingin memperdalam skill coding anak...",
            style=discord.TextStyle.paragraph,
            max_length=200,
            required=True
        )
        self.add_item(self.custom_input)

    async def on_submit(self, interaction: discord.Interaction):
        custom_text = self.custom_input.value.strip()
        self.wizard_view.reason = f"✍️ {custom_text}"
        self.wizard_view.sync_button_styles()

        try:
            await interaction.response.edit_message(
                embed=self.wizard_view.build_embed(),
                view=self.wizard_view
            )
        except Exception:
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=self.wizard_view.build_embed(),
                view=self.wizard_view
            )


class AlgoHCOnboardingWizardView(View):
    """Wizard formulir onboarding interaktif untuk member Algo HC."""
    def __init__(self, user_id: int):
        super().__init__(timeout=600)
        self.user_id = user_id
        self.role_type: Optional[str] = None      # "parent" or "student"
        self.reason: Optional[str] = None         # text of reason
        self.is_competition: Optional[str] = None # "yes" or "no"
        self.sync_button_styles()

    def sync_button_styles(self):
        # Row 0: Status Radio Buttons
        self.btn_parent.label = "👨‍👩‍👧 Parent"
        self.btn_student.label = "🎓 Student"
        self.btn_parent.style = (
            discord.ButtonStyle.primary if self.role_type == "parent" else discord.ButtonStyle.secondary
        )
        self.btn_student.style = (
            discord.ButtonStyle.primary if self.role_type == "student" else discord.ButtonStyle.secondary
        )

        # Row 2: Lomba Algo Yes/No Buttons
        self.btn_comp_yes.label = "✅ Ya, Ikut Lomba"
        self.btn_comp_no.label = "❌ Tidak / Belum"
        self.btn_comp_yes.style = (
            discord.ButtonStyle.success if self.is_competition == "yes" else discord.ButtonStyle.secondary
        )
        self.btn_comp_no.style = (
            discord.ButtonStyle.danger if self.is_competition == "no" else discord.ButtonStyle.secondary
        )

        # Row 3: Submit Button
        is_ready = bool(self.role_type and self.reason and self.is_competition)
        self.btn_submit.disabled = not is_ready
        self.btn_submit.style = discord.ButtonStyle.success if is_ready else discord.ButtonStyle.secondary

    def build_embed(self) -> discord.Embed:
        # Format Status
        if self.role_type == "parent":
            status_text = f"**{ROLE_PARENT}**"
        elif self.role_type == "student":
            status_text = f"**{ROLE_STUDENT}**"
        else:
            status_text = "*Belum dipilih (Klik tombol di bawah)*"

        # Format Alasan
        if self.reason:
            reason_text = f"**{self.reason}**"
        else:
            reason_text = "*Belum dipilih (Pilih dari dropdown menu)*"

        # Format Lomba
        if self.is_competition == "yes":
            comp_text = "**✅ Ya, Ikut Lomba Algo**"
        elif self.is_competition == "no":
            comp_text = "**❌ Tidak / Belum**"
        else:
            comp_text = "*Belum dipilih (Klik Ya atau Tidak)*"

        is_all_filled = bool(self.role_type and self.reason and self.is_competition)

        embed = discord.Embed(
            title="📋 Formulir Onboarding Algo HC 2026",
            description=(
                "Silakan lengkapi formulir di bawah ini untuk membuka akses ke "
                "channel diskusi & pengumuman:\n\n"
                f"**1. Status Anda:**\n{status_text}\n\n"
                f"**2. Alasan Bergabung:**\n{reason_text}\n\n"
                f"**3. Keikutsertaan Lomba Algo:**\n{comp_text}\n\n"
                + (
                    "✨ **Semua pertanyaan sudah terisi lengkap!** Silakan klik tombol hijau "
                    "**🚀 Simpan & Buka Akses Channel** di bawah."
                    if is_all_filled
                    else "⚠️ *Harap lengkapi semua pertanyaan di atas agar tombol simpan dapat diaktifkan.*"
                )
            ),
            color=0x2ecc71 if is_all_filled else 0x3498db
        )
        embed.set_footer(text="Data hanya dapat dilihat oleh Anda & Moderator.")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Menu onboarding ini khusus untuk pengguna yang membukanya.",
                ephemeral=True
            )
            return False
        return True

    # ROW 0: Question 1 (Status: Parent / Student)
    @button(label="👨‍👩‍👧 Parent", style=discord.ButtonStyle.secondary, row=0, custom_id="wizard_btn_parent")
    async def btn_parent(self, interaction: discord.Interaction, btn: Button):
        self.role_type = "parent"
        self.sync_button_styles()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @button(label="🎓 Student", style=discord.ButtonStyle.secondary, row=0, custom_id="wizard_btn_student")
    async def btn_student(self, interaction: discord.Interaction, btn: Button):
        self.role_type = "student"
        self.sync_button_styles()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # ROW 1: Question 2 (Alasan Join Select Menu)
    @select(
        row=1,
        placeholder="Pilih Alasan Bergabung...",
        custom_id="wizard_select_reason",
        options=[
            discord.SelectOption(
                label="Persiapan Lomba Coding / Olimpiade",
                value="lomba_coding",
                emoji="🏆",
                description="Mempersiapkan diri atau anak untuk kompetisi"
            ),
            discord.SelectOption(
                label="Mengasah Logika & Pemrograman",
                value="asah_logika",
                emoji="💡",
                description="Meningkatkan skill dan minat teknologi"
            ),
            discord.SelectOption(
                label="Rekomendasi dari Guru / Sekolah",
                value="rekomendasi_sekolah",
                emoji="🏫",
                description="Mendapat arahan dari pihak sekolah/mentor"
            ),
            discord.SelectOption(
                label="Mencari Info Algo Hackathon",
                value="info_algo",
                emoji="📢",
                description="Ingin mengetahui detail acara & update terbaru"
            ),
            discord.SelectOption(
                label="Lainnya / Other (Tulis Sendiri)",
                value="custom_reason",
                emoji="✍️",
                description="Tulis alasan khusus Anda sendiri"
            ),
        ]
    )
    async def select_reason(self, interaction: discord.Interaction, sel: Select):
        val = sel.values[0]
        if val == "custom_reason":
            await interaction.response.send_modal(CustomReasonModal(wizard_view=self))
            return

        self.reason = REASON_MAP.get(val, val)
        self.sync_button_styles()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # ROW 2: Question 3 (Ikut Lomba Algo? Yes / No)
    @button(label="✅ Ya, Ikut Lomba", style=discord.ButtonStyle.secondary, row=2, custom_id="wizard_btn_comp_yes")
    async def btn_comp_yes(self, interaction: discord.Interaction, btn: Button):
        self.is_competition = "yes"
        self.sync_button_styles()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @button(label="❌ Tidak / Belum", style=discord.ButtonStyle.secondary, row=2, custom_id="wizard_btn_comp_no")
    async def btn_comp_no(self, interaction: discord.Interaction, btn: Button):
        self.is_competition = "no"
        self.sync_button_styles()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # ROW 3: Submit
    @button(label="🚀 Simpan & Buka Akses Channel", style=discord.ButtonStyle.secondary, row=3, disabled=True, custom_id="wizard_btn_submit")
    async def btn_submit(self, interaction: discord.Interaction, btn: Button):
        if not (self.role_type and self.reason and self.is_competition):
            await interaction.response.send_message(
                "⚠️ Mohon lengkapi ketiga pertanyaan di atas sebelum menyimpan data.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = interaction.user
        if not guild or not isinstance(member, discord.Member):
            await interaction.followup.send("❌ Error: Interaksi harus dilakukan di dalam server.", ephemeral=True)
            return

        target_role_name = ROLE_PARENT if self.role_type == "parent" else ROLE_STUDENT
        opposite_role_name = ROLE_STUDENT if self.role_type == "parent" else ROLE_PARENT

        # Cari/buat role yang sesuai
        algo_role = await get_or_create_role(guild, ALGO_HC_ROLE, "algo")
        target_role = await get_or_create_role(guild, target_role_name, self.role_type)
        opposite_role = find_role_resilient(guild, opposite_role_name)

        # Update role member
        roles_to_add = []
        if algo_role and algo_role not in member.roles:
            roles_to_add.append(algo_role)
        if target_role and target_role not in member.roles:
            roles_to_add.append(target_role)

        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason="Algo HC Onboarding completed")
            except Exception as e:
                print(f"❌ Gagal memberikan role ke {member.name}: {e}")

        # Hapus role kebalikan jika user sebelumnya memilikinya
        if opposite_role and opposite_role in member.roles:
            try:
                await member.remove_roles(opposite_role, reason="Algo HC Onboarding status switch")
            except Exception as e:
                print(f"⚠️ Gagal menghapus role lama {opposite_role.name}: {e}")

        # Kirim notifikasi log ke #member-log atau log channel
        await send_onboarding_log(guild, member, self.role_type, self.reason or "-", self.is_competition or "-")

        # Kirim sambutan di channel discussion Algo HC
        await send_welcome_in_discussion(guild, member, target_role_name)

        # Sukses response ke user
        success_embed = discord.Embed(
            title="🎉 Onboarding Algo HC Berhasil!",
            description=(
                f"Terima kasih telah mengisi formulir onboarding, {member.mention}!\n\n"
                f"🏷️ **Role Anda:** `{target_role_name}` & `{ALGO_HC_ROLE}`\n"
                f"🔓 **Akses Terbuka:** Channel diskusi (**#discussion**) dan pengumuman (**#announcement**) "
                f"kini sudah dapat Anda akses!\n\n"
                f"Silakan langsung menuju channel **#discussion** untuk menyapa teman-teman lainnya ya! 🚀"
            ),
            color=0x2ecc71
        )
        await interaction.followup.send(embed=success_embed, ephemeral=True)


class AlgoHCOnboardingLaunchView(View):
    """View panel permanen yang dipasang di channel #onboarding."""
    def __init__(self):
        super().__init__(timeout=None)

    @button(
        label="📝 Mulai Onboarding Algo HC 2026",
        style=discord.ButtonStyle.green,
        custom_id="btn_launch_algo_hc_onboarding",
        emoji="📝"
    )
    async def btn_launch_onboarding(self, interaction: discord.Interaction, btn: Button):
        # Tampilkan formulir interaktif (Radio button + Dropdown + Other modal)
        wizard = AlgoHCOnboardingWizardView(user_id=interaction.user.id)
        embed = wizard.build_embed()
        await interaction.response.send_message(embed=embed, view=wizard, ephemeral=True)


async def ensure_onboarding_panel(channel: discord.TextChannel):
    """Pastikan panel onboarding terpasang di channel tanpa duplikasi."""
    try:
        async for message in channel.history(limit=20):
            if message.author == channel.guild.me and message.embeds:
                if message.embeds[0].title == "📋 Onboarding Algo HC 2026":
                    return
    except Exception as e:
        print(f"⚠️ Gagal cek message history di channel {channel.name}: {e}")

    embed = discord.Embed(
        title="📋 Onboarding Algo HC 2026",
        description=(
            "Halo dan selamat datang di Discord **Algorithmics** & **Algo HC 2026**! 👋\n\n"
            "Untuk membuka akses penuh ke channel diskusi (**#discussion**) dan "
            "pengumuman (**#announcement**), silakan lengkapi 3 pertanyaan onboarding berikut:\n\n"
            "1️⃣ **Status Anda:** Pilih Parent atau Student *(Radio Button)*\n"
            "2️⃣ **Alasan Bergabung:** Pilih opsi atau isi sendiri *(Dropdown + Other)*\n"
            "3️⃣ **Keikutsertaan Lomba:** Ya atau Tidak *(Radio Button)*\n\n"
            "👇 **Klik tombol di bawah untuk mulai mengisi data:**\n"
            "*(Formulir ini bersifat pribadi dan hanya terlihat oleh Anda)*"
        ),
        color=0x3498db
    )
    embed.set_footer(text="Algorithmics Discord Bot • Algo HC 2026")

    try:
        await channel.send(embed=embed, view=AlgoHCOnboardingLaunchView())
        print(f"✅ Panel onboarding berhasil dipasang di #{channel.name}")
    except Exception as e:
        print(f"❌ Gagal mengirim panel onboarding di #{channel.name}: {e}")
