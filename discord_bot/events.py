import discord
from discord_bot.bot import bot
from services.google_sheet import sheet
from config import SPREADSHEET_ID, LOG_SHEET

@bot.event
async def on_ready():
    print(f"✅ Bot aktif sebagai {bot.user}")

@bot.event
async def on_member_join(member):
    try:
        await member.send(
            "👋 Selamat datang!\n\n"
            "Verifikasi via DM:\n"
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