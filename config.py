import os
import discord
from dotenv import load_dotenv

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

# Course → Role map
COURSE_ROLE_MAP = {
    "visual programming": "Visual Programming",
    "game design": "Game Design",
    "python": "Python"
}