import discord # type: ignore
from discord.ext import commands # type: ignore
from discord_bot.bot import bot
from services.google_sheet import (
    get_user_log_status,
)

@bot.command()
async def test(ctx):
    print("TEST COMMAND CALLED")
    await ctx.send("✅ Test berhasil!")

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

@bot.command()
@commands.has_permissions(administrator=True)
async def sendverify(ctx):
    from discord_bot.verify_ui import VerifyView

    embed = discord.Embed(
        title="🎓 Student Verification",
        description="Klik tombol di bawah untuk verifikasi akun kamu.",
        color=0x2ecc71
    )

    await ctx.send(embed=embed, view=VerifyView())