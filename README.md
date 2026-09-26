# CC TOOL

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Playwright-Chromium-green?style=for-the-badge&logo=playwright&logoColor=white" alt="Playwright"/>
  <img src="https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram"/>
  <img src="https://img.shields.io/badge/Proxy-SOCKS5%20%7C%20HTTP-orange?style=for-the-badge" alt="Proxy"/>
</p>

<p align="center">
  <b>CHECKER</b> · <b>KILLER</b> · <b>MASTER</b> · <b>PROXY CHECK</b><br/>
  Local terminal + full Telegram remote control
</p>

```
 /$$$$$$   /$$$$$$        /$$$$$$$$ /$$$$$$   /$$$$$$  /$$       /$$   /$$ /$$$$$$ /$$$$$$$$
 /$$__  $$ /$$__  $$      |__  $$__//$$__  $$ /$$__  $$| $$      | $$  /$$/|_  $$_/|__  $$__/
| $$  \__/| $$  \__/         | $$  | $$  \ $$| $$  \ $$| $$      | $$ /$$/   | $$     | $$   
| $$      | $$               | $$  | $$  | $$| $$  | $$| $$      | $$$$$/    | $$     | $$   
| $$      | $$               | $$  | $$  | $$| $$  | $$| $$      | $$  $$    | $$     | $$   
| $$    $$| $$    $$         | $$  | $$  | $$| $$  | $$| $$      | $$\  $$   | $$     | $$   
|  $$$$$$/|  $$$$$$/         | $$  |  $$$$$$/|  $$$$$$/| $$$$$$$$| $$ \  $$ /$$$$$$   | $$   
 \______/  \______/          |__/   \______/  \______/ |________/|__/  \__/|______/   |__/   
```

---
<video 
  width="640" 
  height="360" 
  controls 
  preload="metadata"
  poster="path/to/poster-image.jpg">
  <source src="https://raw.githubusercontent.com/somratchandraroy/cc-toolkit/demo/preview.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>   
## Features

| Mode | Description |
|------|-------------|
| **CHECKER** | Standard card check (`hits_per_card = 1`) |
| **KILLER** | Multi-hit mode (default 25 hits, separate URL) |
| **MASTER** | Read `bins.txt` → generate Luhn cards in batches → check → stop at min lives |
| **PROXY CHECK** | Health + latency + suitability report for every proxy |

**Also included**

- SOCKS5 via **pproxy** local HTTP bridge (Chromium-safe)
- Auto-normalize proxy formats (`host:port:user:pass`, `user:pass@host:port`, `socks5://...`)
- Proxy rotation + auto-skip after N failures
- Email rotation + random name/username/country
- Live workflow stages in terminal
- Results: `live.txt` · `dead.txt` · `error.txt` · `unknown.txt` · `log.txt`
- Full **Telegram bot** (buttons, commands, file upload, remote config)

---

## Requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| OS | Windows 10 / Ubuntu 22.04+ | Ubuntu 24.04 VPS or local Windows |
| Python | 3.10+ | 3.11 / 3.12 |
| RAM | 2 GB | 4 GB+ |
| Disk | ~5 GB free | 10 GB+ |
| Network | Outbound HTTPS + SOCKS5 | Stable proxies |

**Python packages**

```text
playwright
pproxy
python-telegram-bot==21.6
python-dotenv
```

---

## Install

```bash
# 1. Folder
mkdir -p ~/cctool && cd ~/cctool

# 2. Venv
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Deps
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium  # Linux only

# 4. Config
cp .env.example .env
# edit .env → TELE_BOT_TOKEN and TELE_ADMIN_IDS
```

### `.env`

```env
TELE_BOT_TOKEN=123456789:AAH_your_bot_token
TELE_ADMIN_IDS=7123456789
```

- Get bot token from [@BotFather](https://t.me/BotFather)
- Get your numeric ID from [@userinfobot](https://t.me/userinfobot)

---

## Files

| File | Role |
|------|------|
| `mass_cc_checker.py` | Main tool |
| `data.txt` | Cards for CHECKER / KILLER |
| `proxy.txt` | Proxy list |
| `email.txt` | Emails (rotation) |
| `bins.txt` | BINs for MASTER |
| `live.txt` | Successful hits (kept) |
| `dead.txt` / `error.txt` / `unknown.txt` | Other results |
| `log.txt` | Stage log |
| `proxy_report.txt` | Proxy analytics output |
| `.env` | Telegram secrets |

### Card format (`data.txt`)

```text
5396890231864625|06|2029|233
5396890003595134|07|2028|506
```

### Proxy formats (`proxy.txt`) — all accepted

```text
host:port:user:pass
user:pass@host:port
socks5://user:pass@host:port
socks5://host:port:user:pass
http://user:pass@host:port
```

### BIN format (`bins.txt`)

```text
539689
539689|10|2030
539689|10|2030|123
```

---

## Run

### Local / server terminal

```bash
cd ~/cctool
source venv/bin/activate
python mass_cc_checker.py
```

You get the mode menu **and** Telegram bot in the background.

### 24×7 with tmux

```bash
tmux new -s cctool
cd ~/cctool && source venv/bin/activate
python mass_cc_checker.py
# Detach: Ctrl+B then D
# Reattach: tmux attach -t cctool
```

### Headless on VPS

In menu or Telegram:

```text
/set headless true
```

---

## Telegram control

After `/start` you get buttons:

```text
▶ Checker   ▶ Killer   ▶ Master
📊 Analytics  ⚙️ Config  📁 Files
🔌 Proxies  🩺 Proxy Check  ⏹ Stop
❓ Help
```

### Core commands

| Command | Action |
|---------|--------|
| `/menu` | Show buttons |
| `/help` | Full help |
| `/analytics` | Live / dead / error stats |
| `/config` | All settings |
| `/set key value` | Change any setting |
| `/run checker\|killer\|master` | Start |
| `/stop` | Stop after current card |
| `/files` | List files |
| `/get live.txt` | Tail a file |
| `/clear live\|dead\|error\|unknown\|log` | Wipe file |
| `/proxies` | Proxy count + sample |
| `/proxy_check` | Health test |

### Quick config

```text
/set_headless true
/set_hits 1
/set_timeout 45000
/set_delay 0.5
/set_minlive 100
/set_cards_per_bin 200
/set_bins_per_batch 3
/set_proxy_rot true
/set_email_rot true
/set_random_id true
/set_just_live true
/set_url https://...
/set_killer_url https://...
```

### Upload files

Send a document named:

- `proxy.txt`
- `email.txt`
- `bins.txt`
- `data.txt` / `cards.txt`

---

## MASTER mode logic

1. Load all lines from `bins.txt`
2. Take **N BINs per batch** (default 3)
3. Generate **M Luhn cards per BIN** (default 200)
4. Run checker on that batch
5. Keep **live.txt** · delete dead/error/unknown if enabled
6. Next batch…
7. Stop when **min live cards** reached (`just_need_live = true`, default target 100)

All of this is configurable from the menu or Telegram.

---

## Proxy engine

- Upstream **SOCKS5** (with auth) → local **pproxy** → Chromium HTTP proxy
- Health check before each browser launch
- Auto-skip proxy after consecutive failures
- `/proxy_check` writes `proxy_report.txt` and `proxy_good.txt`

---

## System recommendations

| Use | Spec |
|-----|------|
| Own PC | Windows, 8 GB RAM, GUI debug |
| Light VPS | 2 GB RAM, Ubuntu, headless |
| MASTER long runs | 4 GB RAM, Oracle Free / small paid VPS |
| Always-on | `tmux` or systemd service |

**Free VPS tip:** Oracle Cloud Always Free (if capacity available) is usually the strongest free option for this workload.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No Telegram replies | Check `.env` token, `/start`, process running |
| Unauthorized | Fix `TELE_ADMIN_IDS` numeric ID |
| `ERR_EMPTY_RESPONSE` | Proxy IP dead → `/proxy_check`, rotate proxies |
| Timeouts | Raise `/set_timeout 60000`, slower proxies |
| Stop/restart messy | Wait for **Run finished** before `/run` again |
| Playwright missing | `playwright install chromium` + `install-deps` |

---

## Disclaimer

This tool is for **authorized testing**, education, and your own systems only.  
Unauthorized card testing or payment abuse is illegal. You are responsible for how you use it.

---

<p align="center">
  <b>CC TOOL</b> — terminal + Telegram · checker · killer · master<br/>
  <img src="https://img.shields.io/badge/status-ready-brightgreen?style=flat-square" alt="status"/>
</p>
