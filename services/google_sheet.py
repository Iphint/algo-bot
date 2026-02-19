from datetime import datetime
import json
import os
from dotenv import load_dotenv # type: ignore
from google.oauth2 import service_account # type: ignore
from googleapiclient.discovery import build # type: ignore
from config import SCOPES, SPREADSHEET_ID, STUDENT_SHEET, LOG_SHEET

load_dotenv()

credentials_info = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
creds = service_account.Credentials.from_service_account_info(
    credentials_info, scopes=SCOPES
)

service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

def get_student_by_username_password(username, password):
    res = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{STUDENT_SHEET}!A:Z"
    ).execute()

    rows = res.get("values", [])
    headers = rows[0]

    for row in rows[1:]:
        data = dict(zip(headers, row))
        if (
            data.get("username", "").lower() == username.lower()
            and data.get("password") == password
        ):
            return {
                "student_id": data.get("student_id"),
                "username": data.get("username"),
                "password": data.get("password"),
                "course": data.get("Course", "").lower().strip()
            }
    return None


def get_user_log_status(discord_id):
    res = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{LOG_SHEET}!A:G"
    ).execute()

    for row in res.get("values", [])[1:]:
        if len(row) > 6 and row[3] == str(discord_id):
            return row[6]
    return None


def log_discord_join(student, member):
    res = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{LOG_SHEET}!A:G"
    ).execute()

    rows = res.get("values", [])

    for idx, row in enumerate(rows[1:], start=2):
        if len(row) > 3 and row[3] == str(member.id):
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{LOG_SHEET}!G{idx}",
                valueInputOption="RAW",
                body={"values": [["ACTIVE"]]}
            ).execute()
            return

    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{LOG_SHEET}!A:G",
        valueInputOption="RAW",
        body={"values": [[
            student["username"],
            student["password"],
            student["student_id"],
            str(member.id),
            member.name,
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "ACTIVE"
        ]]}
    ).execute()