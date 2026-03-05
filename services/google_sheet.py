from datetime import datetime
from google.oauth2 import service_account # type: ignore
from googleapiclient.discovery import build # type: ignore
from config import SCOPES, SPREADSHEET_ID, STUDENT_SHEET, LOG_SHEET

creds = service_account.Credentials.from_service_account_file(
    "creds.json",
    scopes=SCOPES
)

service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

user_row_cache = {}

def update_status_by_discord_id(discord_id, new_status):
    global user_row_cache
    if discord_id not in user_row_cache:
        print("ID tidak ada di cache, scanning sekali...")
        res = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{LOG_SHEET}!A:G"
        ).execute()

        rows = res.get("values", [])

        for index, row in enumerate(rows[1:], start=2):
            if len(row) > 3 and str(row[3]).strip() == str(discord_id):
                user_row_cache[discord_id] = index
                break
        else:
            print("❌ ID tidak ditemukan di sheet")
            return False

    row_number = user_row_cache[discord_id]

    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{LOG_SHEET}!G{row_number}",
        valueInputOption="RAW",
        body={"values": [[new_status]]}
    ).execute()

    print(f"✅ Status updated to {new_status} (fast mode)")
    return True

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

    if not rows:
        return

    headers = rows[0]

    username_col = 0
    student_id_col = 2
    discord_id_col = 3
    discord_username_col = 4
    joined_col = 5
    status_col = 6

    for idx, row in enumerate(rows[1:], start=2):
        if len(row) > student_id_col:
            existing_username = row[username_col]
            existing_student_id = row[student_id_col]
            if (
                existing_username == student["username"]
                or existing_student_id == student["student_id"]
            ):
                sheet.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"{LOG_SHEET}!A{idx}:G{idx}",
                    valueInputOption="RAW",
                    body={
                        "values": [[
                            student["username"],
                            student["password"],
                            student["student_id"],
                            str(member.id),
                            member.name,
                            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                            "ACTIVE"
                        ]]
                    }
                ).execute()
                return
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{LOG_SHEET}!A:G",
        valueInputOption="RAW",
        body={
            "values": [[
                student["username"],
                student["password"],
                student["student_id"],
                str(member.id),
                member.name,
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "ACTIVE"
            ]]
        }
    ).execute()

def get_student_by_discord_id(discord_id):
    res = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{LOG_SHEET}!A:G"
    ).execute()

    rows = res.get("values", [])

    if not rows:
        return None

    headers = rows[0]

    for row in rows[1:]:
        if len(row) > 6 and row[3] == str(discord_id) and row[6] == "ACTIVE":
            return {
                "username": row[0],
                "password": row[1],
                "student_id": row[2],
                "course": ""
            }

    return None