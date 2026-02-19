import discord # type: ignore
from discord_bot.bot import bot
from services.google_sheet import (
    get_student_by_username_password,
    get_user_log_status,
    log_discord_join
)
from discord_bot.roles import assign_course_role

@bot.command()
async def verify(ctx, username: str, password: str):
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.message.delete()
        await ctx.author.send("⚠️ Gunakan di DM.")
        return

    guild = bot.guilds[0]
    member = guild.get_member(ctx.author.id)

    if get_user_log_status(member.id) == "ACTIVE":
        await ctx.author.send("✅ Sudah terverifikasi.")
        return

    student = get_student_by_username_password(username, password)
    if not student:
        await ctx.author.send("❌ Data salah.")
        return

    log_discord_join(student, member)

    verified_role = discord.utils.get(guild.roles, name="Verified")
    if verified_role:
        await member.add_roles(verified_role)

    await assign_course_role(member, student["course"])

    await ctx.author.send(
        f"✅ Verifikasi berhasil!\n📘 Course: **{student['course']}**"
    )