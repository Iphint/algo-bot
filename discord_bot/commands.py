import discord # type: ignore
from discord.ext import commands # type: ignore
import asyncio
from discord_bot.bot import bot
from services.google_sheet import (
    get_student_by_username_password,
    get_user_log_status,
    log_discord_join
)
from discord_bot.roles import assign_course_role

@bot.command()
async def test(ctx):
    print("TEST COMMAND CALLED")
    await ctx.send("✅ Test berhasil!")

@bot.command()
async def verify(ctx, username: str, password: str):
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.message.delete()
        await ctx.author.send("⚠️ Gunakan di DM.")
        return

    guild = bot.guilds[0]
    member = await guild.fetch_member(ctx.author.id)

    loop = asyncio.get_event_loop()

    try:
        status = await loop.run_in_executor(
            None, get_user_log_status, member.id
        )

        if status == "ACTIVE":
            await ctx.author.send("✅ Sudah terverifikasi.")
            return

        student = await loop.run_in_executor(
            None,
            get_student_by_username_password,
            username,
            password
        )

    except Exception as e:
        await ctx.author.send(f"❌ Error Google Sheet:\n{e}")
        print("GOOGLE ERROR:", e)
        return

    if not student:
        await ctx.author.send("❌ Data salah.")
        return

    await loop.run_in_executor(
        None,
        log_discord_join,
        student,
        member
    )

    verified_role = discord.utils.get(guild.roles, name="Verified")
    if verified_role:
        await member.add_roles(verified_role)

    unverified_role = discord.utils.get(guild.roles, name="Unverified")
    if unverified_role:
        await member.remove_roles(unverified_role)
        
    await assign_course_role(member, student["course"])

    await ctx.author.send(
        f"✅ Verifikasi berhasil!\n📘 Course: **{student['course']}**"
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def recheck(ctx):
    guild = ctx.guild
    count = 0

    for member in guild.members:
        if member.bot:
            continue

        status = get_user_log_status(member.id)

        if status == "ACTIVE":
            verified_role = discord.utils.get(guild.roles, name="Verified")
            if verified_role and verified_role not in member.roles:
                await member.add_roles(verified_role)
                count += 1

    await ctx.send(f"✅ Recheck selesai. {count} member diperbaiki.")