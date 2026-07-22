# AGENTS.md

## Run

```bash
python main.py
```

## Setup

Copy `.env.example` (create if missing) and fill:
- `DISCORD_TOKEN` — bot token
- `SPREADSHEET_ID` — Google Sheets ID

Place `credentials.json` (Google service account) in root. Sheet must have tabs: `students`, `ps`, `discord_log`, `report-center`, `student-reports`, `progress-reports`, `warnings`.

```bash
pip install -r requirements.txt
```

## Architecture

- `main.py` — entrypoint; imports events and commands, runs bot
- `config.py` — env vars, intents, role/sheet maps
- `discord_bot/bot.py` — `commands.Bot` instance
- `discord_bot/commands.py` — prefix commands (`!test`, `!recheck`, `!progress`, `!joined`, `!intro_stats`)
- `discord_bot/events.py` — `on_ready`, `on_member_join`, `on_member_remove`, `on_message`, pending-intro checker loop
- `discord_bot/report_ui.py` — safety + student report modals
- `discord_bot/roles.py` — course-to-role assignment based on `COURSE_ROLE_MAP`
- `discord_bot/profanity_filter.py` — profanity detection (ID + EN word lists)
- `services/google_sheet.py` — all Google Sheets API calls

## Key conventions

- Commands use prefix `!` (not slash commands, despite `tree.sync` in `on_ready`)
- Role names in config must match Discord server role names exactly (e.g. `"🐍 Python Student"`, `"🏅 | Verified Student"`, `"Unverified Student"`)
- `COURSE_ROLE_MAP` does substring matching on course name
- `pending_intro` is an in-memory dict — lost on restart
- `on_member_remove` marks user `INACTIVE` in `discord_log` sheet

## Spam filter

- Runs in `on_message`, skips channels matching `SPAM_SKIP_CHANNELS` in `config.py`
- Detects: rapid-fire (6+ messages in 5s), duplicate messages (3+), mass mentions (5+), suspicious scam domains, spam patterns (fake Nitro/crypto giveaways, shortened URLs), all-caps
- Violations reuse the same `warnings` sheet and warning progression system (1-3 role → 4 timeout 1d → 5 timeout 5d → 6 ban)
- `SpamTracker` class in `discord_bot/spam_filter.py` maintains in-memory per-user message history (auto-cleanup every 5 min)
- To adjust thresholds: edit `SPAM_RATE_LIMIT`, `SPAM_RATE_WINDOW`, etc. in `config.py`
- To add scam domains: edit `SCAM_DOMAINS` in `discord_bot/spam_filter.py`
- To add spam patterns: edit `SPAM_PATTERNS` in `discord_bot/spam_filter.py`

## Profanity filter & warning system

- Filter runs in `on_message`, skips channels with "admin"/"mod" in name, skips roles in `EXEMPT_ROLES`
- Words in `profanity_filter.py` (Indonesian + English lists)
- Warnings persist in `warnings` sheet, cached in memory
- Warning progression:
  - 1-3: assign role `⚠️ Warning 1/2/3`, delete message, show embed
  - 4: timeout 1 day
  - 5: timeout 5 days
  - 6: permanent ban (auto-reset warning count)
- To add words: edit `PROFANITY_LIST_ID` or `PROFANITY_LIST_EN` in `discord_bot/profanity_filter.py`
- To change exempt roles: edit `EXEMPT_ROLES` in `config.py`

## Secrets

Never commit `.env`, `credentials.json`, or `service.json`. They are in `.gitignore`.
