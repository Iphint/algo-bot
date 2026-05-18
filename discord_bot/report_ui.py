import discord  # type: ignore
from discord.ui import Modal, TextInput, View, Button  # type: ignore
from datetime import datetime
from services.google_sheet import append_report

REPORT_CENTER_CHANNEL = "report-center"
STUDENT_REPORT_CHANNEL = "student-reports"


class SafetyReportModal(Modal, title="🚨 Report Spam / Hack / Scam"):
    category = TextInput(
        label="Jenis Laporan",
        placeholder="Spam crypto / akun kena hack / scam link / impersonation",
        required=True,
        max_length=80
    )

    target_user = TextInput(
        label="User yang Dilaporkan",
        placeholder="Tag/nama user yang mencurigakan",
        required=True,
        max_length=100
    )

    evidence = TextInput(
        label="Bukti / Lokasi Kejadian",
        placeholder="Channel, jam kejadian, isi pesan, atau link message",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )

    detail = TextInput(
        label="Detail Tambahan",
        placeholder="Ceritakan kronologinya secara singkat...",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        reporter = interaction.user
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "timestamp": now,
            "report_type": "Safety Report",
            "reporter_name": str(reporter),
            "reporter_id": str(reporter.id),
            "category": self.category.value,
            "target_user": self.target_user.value,
            "title": self.evidence.value,
            "detail": self.detail.value if self.detail.value else "-",
            "status": "OPEN",
        }

        append_report("report-center", data)

        await interaction.followup.send(
            "✅ Safety report berhasil dikirim dan dicatat ke spreadsheet.",
            ephemeral=True
        )


class StudentAccountReportModal(Modal, title="🎓 Report Akun Siswa"):
    student_name = TextInput(
        label="Nama Siswa",
        placeholder="Contoh: Mikail / Putri Nadia / username Algonova",
        required=True,
        max_length=100
    )

    issue_type = TextInput(
        label="Jenis Kendala",
        placeholder="Tidak bisa login / lupa password / salah role / gagal verify",
        required=True,
        max_length=100
    )

    discord_account = TextInput(
        label="Akun Discord Siswa",
        placeholder="Tag Discord atau username Discord siswa",
        required=False,
        max_length=100
    )

    detail = TextInput(
        label="Detail Kendala",
        placeholder="Jelaskan masalah akun siswa secara lengkap...",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        reporter = interaction.user
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "timestamp": now,
            "report_type": "Student Account Report",
            "reporter_name": str(reporter),
            "reporter_id": str(reporter.id),
            "category": self.issue_type.value,
            "target_user": self.discord_account.value if self.discord_account.value else "-",
            "title": self.student_name.value,
            "detail": self.detail.value,
            "status": "OPEN",
        }

        append_report("student-reports", data)

        await interaction.followup.send(
            "✅ Report akun siswa berhasil dikirim dan dicatat ke spreadsheet.",
            ephemeral=True
        )


class ReportCenterView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🚨 Report Spam / Hack / Scam",
        style=discord.ButtonStyle.red,
        custom_id="safety_report_button"
    )
    async def safety_report_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SafetyReportModal())


class StudentReportView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎓 Report Akun Siswa",
        style=discord.ButtonStyle.blurple,
        custom_id="student_account_report_button"
    )
    async def student_account_report_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(StudentAccountReportModal())