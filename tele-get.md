[P]

**How to get `TELE_ADMIN_IDS`**

That value is your **Telegram numeric user ID** (not your @username).

### Method 1 — easiest
1. Open Telegram  
2. Search for **`@userinfobot`**  
3. Start the bot  
4. It replies with your **Id:** number (example: `7123456789`)

### Method 2
1. Search **`@getidsbot`** or **`@RawDataBot`**  
2. Start it  
3. Read the `id` field  

### Put it in `.env`
```env
TELE_BOT_TOKEN=123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELE_ADMIN_IDS=7123456789
```

Multiple admins (comma-separated, no spaces needed):
```env
TELE_ADMIN_IDS=7123456789,6987654321
```

### Notes
- Must be the **number**, not `@name`  
- If `TELE_ADMIN_IDS` is **empty**, anyone who finds your bot can control it  
- After editing `.env`, restart the script  

That’s the ID the tool checks for `/run`, `/set`, `/clear`, etc.