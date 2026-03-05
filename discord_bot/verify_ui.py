import discord
import asyncio
from discord.ui import Modal, TextInput, View, Button
from services.google_sheet import (
    get_student_by_username_password,
    get_user_log_status,
    log_discord_join
)
from discord_bot.roles import assign_course_role


class VerifyModal(Modal, title="🎓 Verifikasi Akun Algonova"):
    username = TextInput(
        label="Username Algonova",
        placeholder="Masukkan username akun kelas Algonova kamu",
        required=True
    )
    password = TextInput(
        label="Password Algonova",
        placeholder="Masukkan password akun kelas Algonova kamu",
        required=True,
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        member = interaction.user
        guild = interaction.guild
        loop = asyncio.get_event_loop()

        # Cek apakah user sudah pernah verifikasi
        status = await loop.run_in_executor(None, get_user_log_status, member.id)
        if status == "ACTIVE":
            await interaction.followup.send(
                "✅ Kamu sudah terverifikasi sebelumnya.\n"
                "Jika ada masalah, hubungi admin.",
                ephemeral=True
            )
            return

        # Validasi kredensial akun Algonova
        student = await loop.run_in_executor(
            None,
            get_student_by_username_password,
            self.username.value,
            self.password.value
        )
        if not student:
            await interaction.followup.send(
                "❌ **Username atau password salah.**\n"
                "Pastikan kamu memasukkan kredensial **akun kelas Algonova**, bukan akun Discord.\n"
                "Hubungi admin jika lupa password.",
                ephemeral=True
            )
            return

        # Catat log join Discord
        await loop.run_in_executor(None, log_discord_join, student, member)

        # Tambah role Verified, hapus role Unverified
        verified_role = discord.utils.get(guild.roles, name="Verified")
        if verified_role:
            await member.add_roles(verified_role)

        unverified_role = discord.utils.get(guild.roles, name="Unverified")
        if unverified_role:
            await member.remove_roles(unverified_role)

        # Assign role sesuai course
        await assign_course_role(member, student["course"])

        await interaction.followup.send(
            f"🎉 **Verifikasi berhasil! Selamat datang di Algonova!**\n\n"
            f"📘 Course kamu: **{student['course']}**\n"
            f"✅ Kamu sekarang punya akses penuh ke channel yang sesuai.",
            ephemeral=True
        )


class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✅ Verifikasi Akun Algonova",
        style=discord.ButtonStyle.green,
        custom_id="verify_button"
    )
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(VerifyModal())