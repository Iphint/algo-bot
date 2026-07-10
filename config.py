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

# Profanity filter - exempt roles (Admin/Owner always exempt)
EXEMPT_ROLES = ["Administrator", "Owner"]

# Profanity filter - exempt user IDs (moderator-specific)
PROFANITY_EXEMPT_IDS = [
    943726651399864330,  # Arifin
    1407622673130983555, # Kak Nad
    1385603832293228658, # Arsa
]

# Warning roles
WARNING_ROLES = {
    1: "⚠️ Warning 1",
    2: "⚠️ Warning 2",
    3: "⚠️ Warning 3",
}

# Spam filter config
SPAM_RATE_LIMIT = 4       # max messages in window (rapid fire)
SPAM_RATE_WINDOW = 5      # window in seconds
SPAM_BURST_LIMIT = 3      # consecutive messages in short window
SPAM_BURST_WINDOW = 2     # short window in seconds
SPAM_DUPLICATE_THRESHOLD = 3
SPAM_MAX_MENTIONS = 5
SPAM_ALL_CAPS_MIN_LEN = 10
SPAM_ALL_CAPS_RATIO = 0.7
SPAM_SKIP_CHANNELS = ["admin", "mod", "logs"]

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