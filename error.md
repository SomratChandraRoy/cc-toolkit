## 🔁 Alternative Commands

### With `sudo` (if the script needs root):

```bash
curl -sL https://raw.githubusercontent.com/SomratChandraRoy/cc-toolkit/main/setup.sh | sudo bash
```

### Download first, then run (safer — inspect before executing):

```bash
curl -sL -o setup.sh https://raw.githubusercontent.com/SomratChandraRoy/cc-toolkit/main/setup.sh
cat setup.sh          # 👀 review the script
chmod +x setup.sh
./setup.sh
```

### Using `wget`:

```bash
wget -qO- https://raw.githubusercontent.com/SomratChandraRoy/cc-toolkit/main/setup.sh | bash
```

### With arguments:

```bash
curl -sL https://raw.githubusercontent.com/SomratChandraRoy/cc-toolkit/main/setup.sh | bash -s -- arg1 arg2
```

---

## 🌐 Access Your Public Preview

After the setup script runs and starts a service on a port (e.g. `8000`), your public preview URL will look like:

```
https://8000-<sandbox-id>.<runner>.daytona.work
```

You can share this link with anyone — no login required (because **Public HTTP Preview** is enabled).

---

## ⚙️ Sandbox Settings Reference

| Parameter | Meaning |
|-----------|---------|
| `auto-stop = 43800` | Sandbox stays alive for ~30 days of inactivity |
| `auto-stop = 0` | Never auto-stops (runs indefinitely) |
| `public = true` | Preview URLs are publicly accessible |
| `public = false` | Only org members can access previews |

---

## 🧹 Cleanup

When you're done:

1. Go to **Sandboxes**
2. Select your sandbox
3. Click **Stop** → **Delete**

Or via CLI:

```bash
daytona delete my-free-vps
```

---

## ⚠️ Important Notes

- **`raw.githubusercontent.com`** — Always use the raw URL, NOT the `github.com/.../blob/...` URL
- **File case sensitivity** — `setup.sh` must match exactly (lowercase)
- **Line endings** — If you get `\r: bad file format`, the script has Windows line endings. Fix in GitHub: Edit file → "Fix whitespace" → Commit
- **Free tier limits** — Daytona free tier may have usage caps; check [pricing](https://www.daytona.io/pricing)
- **Security** — Review the script before piping to `bash` in production

---

## 📁 Repo Structure

```
cc-toolkit/
├── setup.sh              ← The one-liner setup script
├── demo/
│   └── preview.mp4       ← Demo video
└── free-vps.md           ← This file
```

---

## 📝 Quick Reference (Cheat Sheet)

```text
┌─────────────────────────────────────────────────────────┐
│  1. daytona.io → Sign Up (Email/Google/GitHub)         │
│  2. Create Sandbox                                      │
│     • Name: my-free-vps                                 │
│     • Class: daytona-vm-large                           │
│     • Auto-Stop: 43800                                  │
│     • Public HTTP Preview: ✅                           │
│  3. Open Terminal                                       │
│  4. Run:                                                │
│     curl -sL https://raw.githubusercontent.com/        │
│       SomratChandraRoy/cc-toolkit/main/setup.sh | bash  │
└─────────────────────────────────────────────────────────┘
```

---

> Made with ❤️ | [cc-toolkit](https://github.com/SomratChandraRoy/cc-toolkit)
```


