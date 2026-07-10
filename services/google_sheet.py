from datetime import datetime
from google.oauth2 import service_account # type: ignore
from googleapiclient.discovery import build # type: ignore
from config import SCOPES, SPREADSHEET_ID, LOG_SHEET, COURSE_SHEET_MAP, WARNING_SHEET

creds = service_account.Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

user_row_cache = {}
warning_cache = {}

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

def find_student_in_sheet(sheet_name, username, password):
    res = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A:Z"
    ).execute()

    rows = res.get("values", [])
    if not rows:
        return None

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
                "course": data.get("Course", "").lower().strip(),
                "source_sheet": sheet_name
            }
    return None

def get_student_by_username_password(username, password):
    # 1. cek PS dulu (prioritas)
    ps_sheet = COURSE_SHEET_MAP.get("ps")
    student = find_student_in_sheet(ps_sheet, username, password)

    if student:
        return student

    # 2. fallback ke default (students)
    default_sheet = COURSE_SHEET_MAP.get("default")
    return find_student_in_sheet(default_sheet, username, password)

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

def append_report(sheet_name, data):
    values = [[
        data.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        data.get("report_type", ""),
        data.get("reporter_name", ""),
        data.get("reporter_id", ""),
        data.get("category", ""),
        data.get("target_user", ""),
        data.get("title", ""),
        data.get("detail", ""),
        data.get("status", "OPEN"),
    ]]

    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{sheet_name}'!A:I",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values}
    ).execute()

    print(f"✅ Report berhasil ditambahkan ke sheet: {sheet_name}")
    return True

def append_progress_report(data):
    values = [[
        data.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        data.get("report_type", ""),
        data.get("date_range", ""),
        data.get("total_messages", 0),
        data.get("active_users_range", 0),
        data.get("active_users_90d", 0),
        data.get("inactive_users_90d", 0),
        data.get("engagement_depth", 0),
        data.get("active_rate_60d", "0%"),
        data.get("score", 0),
        data.get("active_user_list", ""),
        data.get("inactive_user_list", ""),
        data.get("executed_by", ""),
    ]]

    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="'progress-reports'!A:M",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values}
    ).execute()

    print("✅ Progress report berhasil masuk spreadsheet")
    return True

def append_progress_report(data):
    values = [[
        data.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        data.get("report_type", ""),
        data.get("date_range", ""),
        data.get("total_messages", 0),
        data.get("active_users_range", 0),
        data.get("active_users_90d", 0),
        data.get("inactive_users_90d", 0),
        data.get("engagement_depth", 0),
        data.get("active_rate_60d", "0%"),
        data.get("score", 0),
        data.get("active_user_list", ""),
        data.get("inactive_user_list", ""),
        data.get("executed_by", ""),
    ]]

    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="'progress-reports'!A:M",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values}
    ).execute()

    print("✅ Progress report berhasil masuk spreadsheet")
    return True

def get_joined_students_by_date_range(start_date, end_date):
    res = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{LOG_SHEET}!A:G"
    ).execute()

    rows = res.get("values", [])

    if not rows:
        return []

    joined_students = []

    for row in rows[1:]:
        try:
            username = row[0] if len(row) > 0 else "-"
            student_id = row[2] if len(row) > 2 else "-"
            discord_id = row[3] if len(row) > 3 else "-"
            discord_name = row[4] if len(row) > 4 else "-"
            joined_at = row[5] if len(row) > 5 else "-"
            status = row[6] if len(row) > 6 else "-"

            joined_date = datetime.strptime(joined_at, "%Y-%m-%d %H:%M:%S")

            if start_date <= joined_date < end_date:
                joined_students.append({
                    "username": username,
                    "student_id": student_id,
                    "discord_id": discord_id,
                    "discord_name": discord_name,
                    "joined_at": joined_at,
                    "status": status
                })

        except Exception as e:
            print("❌ Skip row join report:", e)

    return joined_students

def get_user_warning_count(discord_id):
    global warning_cache
    if discord_id in warning_cache:
        return warning_cache[discord_id]

    try:
        res = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{WARNING_SHEET}!A:E"
        ).execute()

        rows = res.get("values", [])
        if not rows:
            return 0

        for row in rows[1:]:
            if len(row) > 1 and str(row[1]) == str(discord_id):
                count = int(row[2]) if row[2] else 0
                warning_cache[discord_id] = count
                return count

    except Exception as e:
        print(f"❌ Error getting warning count: {e}")

    return 0

def increment_warning(discord_id, word_used):
    global warning_cache
    count = get_user_warning_count(discord_id)
    new_count = count + 1

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    try:
        res = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{WARNING_SHEET}!A:E"
        ).execute()

        rows = res.get("values", [])

        found = False
        for idx, row in enumerate(rows[1:], start=2):
            if len(row) > 1 and str(row[1]) == str(discord_id):
                sheet.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"{WARNING_SHEET}!B{idx}:E{idx}",
                    valueInputOption="RAW",
                    body={"values": [[str(discord_id), new_count, word_used, now]]}
                ).execute()
                found = True
                break

        if not found:
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{WARNING_SHEET}!A:E",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [[str(discord_id), discord_id, new_count, word_used, now]]}
            ).execute()

        warning_cache[discord_id] = new_count
        print(f"✅ Warning {new_count}/6 for user {discord_id}")

    except Exception as e:
        print(f"❌ Error incrementing warning: {e}")

    return new_count

def reset_warning(discord_id):
    global warning_cache
    warning_cache[discord_id] = 0

    try:
        res = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{WARNING_SHEET}!A:E"
        ).execute()

        rows = res.get("values", [])
        for idx, row in enumerate(rows[1:], start=2):
            if len(row) > 1 and str(row[1]) == str(discord_id):
                sheet.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"{WARNING_SHEET}!C{idx}",
                    valueInputOption="RAW",
                    body={"values": [["0"]]}
                ).execute()
                break

    except Exception as e:
        print(f"❌ Error resetting warning: {e}")