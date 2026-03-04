import discord # type: ignore
from discord_bot.bot import bot
from services.google_sheet import sheet
from config import SPREADSHEET_ID, LOG_SHEET

@bot.event
async def on_ready():
    print(f"✅ Bot aktif sebagai {bot.user}")

@bot.event
async def on_member_join(member):
    guild = member.guild

    # kasih role Unverified otomatis
    unverified_role = discord.utils.get(guild.roles, name="Unverified")
    if unverified_role:
        await member.add_roles(unverified_role)

    # cek apakah sudah pernah verified
    from services.google_sheet import get_user_log_status

    if get_user_log_status(member.id) == "ACTIVE":
        from services.google_sheet import get_student_by_discord_id
        student = get_student_by_discord_id(member.id)

        if student:
            verified_role = discord.utils.get(guild.roles, name="Verified")
            if verified_role:
                await member.add_roles(verified_role)

            from discord_bot.roles import assign_course_role
            await assign_course_role(member, student["course"])

            if unverified_role:
                await member.remove_roles(unverified_role)

    try:
        await member.send(
            "👋 Selamat datang!\n\n"
            "Silakan verifikasi:\n"
            "`!verify username password`"
        )
    except:
        pass


@bot.event
async def on_member_remove(member):
    res = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{LOG_SHEET}!A:G"
    ).execute()

    for idx, row in enumerate(res.get("values", [])[1:], start=2):
        if len(row) > 3 and row[3] == str(member.id):
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{LOG_SHEET}!G{idx}",
                valueInputOption="RAW",
                body={"values": [["INACTIVE"]]}
            ).execute()
            break