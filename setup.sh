#!/bin/bash

# ==========================================
# Error Handling Function
# ==========================================
handle_error() {
    echo ""
    echo "=========================================="
    echo "❌ ERROR: Installation failed!"
    echo "Failed on line $1 during command: '$2'"
    echo "=========================================="
    exit 1
}

# Trap any command failure and send to error handler
trap 'handle_error ${LINENO} "$BASH_COMMAND"' ERR

# Detect sudo availability (useful if running in Docker as root)
SUDO=""
if [ "$EUID" -ne 0 ] && command -v sudo &> /dev/null; then
    SUDO="sudo"
fi

echo "🚀 Starting CC-Toolkit Automated Setup..."

# ==========================================
# 1. Install System Packages & Editing Tools
# ==========================================
echo "📦 Updating package list and installing system tools (git, tmux, nano)..."
$SUDO apt-get update -y
$SUDO apt-get install -y git tmux nano python3 python3-pip python3-venv

# ==========================================
# 2. Clone Repository
# ==========================================
REPO_URL="https://github.com/SomratChandraRoy/cc-toolkit"
REPO_DIR="cc-toolkit"

if [ -d "$REPO_DIR" ]; then
    echo "📂 Directory '$REPO_DIR' already exists. Navigating inside..."
    cd "$REPO_DIR"
else
    echo "📥 Cloning repository: $REPO_URL..."
    git clone "$REPO_URL"
    cd "$REPO_DIR"
fi

# ==========================================
# 3. Install Python Dependencies
# ==========================================
echo "🐍 Installing Python libraries..."

# Flag check for PEP 668 externally-managed environments
PIP_FLAGS="--break-system-packages"
if ! python3 -m pip install --help | grep -q "break-system-packages"; then
    PIP_FLAGS=""
fi

python3 -m pip install $PIP_FLAGS \
    "playwright>=1.40.0" \
    "pproxy>=2.4.0" \
    "python-telegram-bot==21.6" \
    "python-dotenv>=1.0.0"

if [ -f "requirements.txt" ]; then
    echo "📋 Installing dependencies from requirements.txt..."
    python3 -m pip install $PIP_FLAGS -r requirements.txt
fi

echo "🌐 Installing Playwright browsers and dependencies..."
python3 -m playwright install --with-deps || true

# ==========================================
# 4. Prompt User for Credentials & Create .env
# ==========================================
echo ""
echo "=========================================="
echo "⚙️ Telegram Configuration Setup"
echo "=========================================="

read -p "Enter Telegram Bot Token: " USER_BOT_TOKEN
read -p "Enter Telegram Admin ID: " USER_ADMIN_ID

if [ -z "$USER_BOT_TOKEN" ] || [ -z "$USER_ADMIN_ID" ]; then
    echo "❌ Error: Both Bot Token and Admin ID are required!"
    exit 1
fi

echo "📝 Creating .env file..."
cat <<EOF > .env
# Copy to .env and fill values
TELE_BOT_TOKEN=${USER_BOT_TOKEN}
TELE_ADMIN_IDS=${USER_ADMIN_ID}
EOF

echo "✅ .env file successfully saved."

# ==========================================
# 5. Check main.py & Start inside tmux
# ==========================================
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py does not exist in $(pwd)!"
    exit 1
fi

echo "🔄 Launching process in background tmux session 'cctool'..."

# Kill existing session if running
tmux kill-session -t cctool 2>/dev/null || true

# Launch script in a detached tmux session (-d auto-detaches like Ctrl+B then D)
tmux new-session -d -s cctool "python3 main.py"

# Verify tmux session started
if tmux has-session -t cctool 2>/dev/null; then
    echo ""
    echo "=========================================="
    echo "cc toolkit is ready for use go telegrame bot"
    echo "=========================================="
    echo "ℹ️ Session 'cctool' is actively running in the background."
    echo "ℹ️ To view or interact with it: tmux attach -t cctool"
    echo "=========================================="
else
    echo "❌ Failed to start the tmux session 'cctool'."
    exit 1
fi