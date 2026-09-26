[P]

**Run CC TOOL on server + control from Telegram**

---

### 1. Server setup (one time)

**SSH into your VPS (Ubuntu recommended):**
```bash
ssh root@YOUR_SERVER_IP
```

**Install system packages:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

**Create folder + venv:**
```bash
mkdir -p ~/cctool && cd ~/cctool
python3 -m venv venv
source venv/bin/activate
```

**Copy your files into `~/cctool`:**
- `mass_cc_checker.py`
- `requirements.txt`
- `.env`
- `proxy.txt` / `data.txt` / `email.txt` / `bins.txt` (as needed)

**Install Python deps:**
```bash
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
```

**`.env` must look like:**
```env
TELE_BOT_TOKEN=123456789:AAH_your_real_token
TELE_ADMIN_IDS=your_numeric_id
```

---

### 2. First run (test)

```bash
cd ~/cctool
source venv/bin/activate
python mass_cc_checker.py
```

You should see:
- Banner / menu on the server terminal  
- `[+] Telegram bot polling...`

Leave this process running for a quick test, then use Telegram.

**Better for 24×7:** run inside `tmux` or `screen`:

```bash
sudo apt install -y tmux
tmux new -s cctool
cd ~/cctool && source venv/bin/activate
python mass_cc_checker.py
```

Detach: `Ctrl+B` then `D`  
Reattach later: `tmux attach -t cctool`

---

### 3. Telegram — first steps

1. Open Telegram → open **your bot**  
2. Send: `/start`  
3. Send: `/help`  
4. Send: `/analytics`  

If you get “Unauthorized”, `TELE_ADMIN_IDS` is wrong (use numeric ID from `@userinfobot`).

---

### 4. All important commands

| Command | What it does |
|---------|----------------|
| `/start` | Link this chat to the bot |
| `/help` | Command list |
| `/status` or `/analytics` | Live / dead / error counts + session stats |
| `/config` | Show current settings |
| `/set key value` | Change setting (examples below) |
| `/run checker` | Start checker mode |
| `/run killer` | Start killer mode |
| `/run master` | Start master (bins → generate → check) |
| `/stop` | Stop after current card |
| `/files` | List files on server |
| `/get live.txt` | Show last lines of a file |
| `/get dead.txt` | Same for dead |
| `/get log.txt` | Recent log |
| `/get proxy.txt` | Proxy list tail |
| `/clear live` | Empty live.txt |
| `/clear dead` | Empty dead.txt |
| `/clear error` | Empty error.txt |
| `/clear unknown` | Empty unknown.txt |
| `/clear log` | Empty log.txt |
| `/delete_line proxy.txt badtext` | Remove matching lines |
| `/proxies` | How many proxies + sample |
| `/proxy_check` | Health-test proxies (up to 25) |

**Upload files:**  
Send a document named like:
- `proxy.txt`
- `email.txt`
- `bins.txt`
- `data.txt` / `cards.txt`

Bot saves it on the server automatically.

---

### 5. Useful `/set` examples

```text
/set headless true
/set hits_per_card 1
/set timeout_ms 45000
/set proxy_rotation true
/set just_need_live true
/set min_live_cards 100
/set cards_per_bin 200
/set bins_per_batch 3
/set delay_between_hits 0.5
/set data_file data.txt
/set proxy_file proxy.txt
/set bins_file bins.txt
```

Then `/config` to verify.

---

### 6. Typical workflow from phone

1. Upload `proxy.txt` (document)  
2. `/proxy_check` → wait for result  
3. Upload `data.txt` or `bins.txt`  
4. `/set headless true`  
5. `/run checker`  (or `master` / `killer`)  
6. `/analytics` anytime  
7. `/get live.txt` to see hits  
8. `/stop` when you want to halt  

---

### 7. Optional: systemd service (auto-start on reboot)

```bash
sudo nano /etc/systemd/system/cctool.service
```

Paste:
```ini
[Unit]
Description=CC TOOL
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cctool
ExecStart=/root/cctool/venv/bin/python /root/cctool/mass_cc_checker.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

(Adjust paths if your folder/user differ.)

```bash
sudo systemctl daemon-reload
sudo systemctl enable cctool
sudo systemctl start cctool
sudo systemctl status cctool
```

Logs: `journalctl -u cctool -f`

---

### 8. Checklist if something fails

| Problem | Fix |
|---------|-----|
| Bot never replies | Token wrong / bot not started with `/start` / process not running |
| Unauthorized | Fix `TELE_ADMIN_IDS` numeric ID, restart script |
| `/run` does nothing | Check server terminal or `journalctl` for Python errors |
| Playwright / browser errors | `playwright install chromium` + `playwright install-deps` |
| Proxy errors | `/proxy_check`, fix `proxy.txt` format |
| Process dies on SSH close | Use `tmux` or systemd |

---

**Minimum path:**  
server has script + `.env` + deps → `python mass_cc_checker.py` (in tmux) → Telegram `/start` → `/run checker` → `/analytics`.