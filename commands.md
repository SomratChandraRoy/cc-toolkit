

Telegram control added. Local menu still works.

**Setup**

1. `.env` next to the script:
```env
TELE_BOT_TOKEN=your_token_here
TELE_ADMIN_IDS=your_telegram_user_id
```
(`TELE_ADMIN_IDS` optional — empty = anyone can use the bot)

2. Install:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Run on your machine or VPS:
```bash
python mass_cc_checker.py
```
→ local menu **and** Telegram bot both active.

---

**Telegram commands**

| Command | Action |
|---------|--------|
| `/start` `/help` | Welcome / command list |
| `/status` `/analytics` | Live stats, session counters, current card |
| `/config` | Show all settings |
| `/set key value` | Change any CONFIG key |
| `/run checker\|killer\|master` | Start mode in background |
| `/stop` | Stop after current card |
| `/files` | List data files + sizes |
| `/get live.txt` | Tail of any allowed file |
| `/clear live\|dead\|error\|unknown\|log` | Wipe file |
| `/delete_line proxy.txt text` | Remove matching lines |
| `/proxies` | Proxy count + sample |
| `/proxy_check` | Health test (up to 25) |
| **Upload document** named `proxy.txt` / `email.txt` / `bins.txt` / `data.txt` | Save file on server |

---

**CRUD**

- **Create/Update:** upload files, `/set`, append via runs  
- **Read:** `/get`, `/analytics`, `/files`, `/config`  
- **Delete:** `/clear`, `/delete_line`  

---

**Both modes**

- **Own machine:** full terminal menu + animations + bot  
- **VPS/server:** same script; control everything from Telegram; use `headless=True`  

Token is read only from `.env` (`TELE_BOT_TOKEN`). Never hardcode it.