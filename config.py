import os
import discord # type: ignore
from dotenv import load_dotenv # type: ignore

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Discord intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Google Sheet
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
STUDENT_SHEET = "students"
LOG_SHEET = "discord_log"
WARNING_SHEET = "warnings"

# Profanity filter - exempt roles
EXEMPT_ROLES = ["Moderator", "Administrator", "Owner"]

# Warning roles
WARNING_ROLES = {
    1: "⚠️ Warning 1",
    2: "⚠️ Warning 2",
    3: "⚠️ Warning 3",
}

# Course → Role map
COURSE_ROLE_MAP = [
    ("python pro", "🐍 Python Student"),
    ("python start", "🐍 Python Student"),
    ("roblox", "Roblox"),
    ("visual", "Visual Programming"),
]

COURSE_SHEET_MAP = {
    "ps": "ps",           
    "default": "students"
}