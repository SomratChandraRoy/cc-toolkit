# 🚀 Free VPS with Daytona + CC Toolkit

> **Instant free Linux VPS** using [Daytona.io](https://www.daytona.io/) + one-command setup.

---

## ✨ What You Get

| Feature | Details |
|---------|---------|
| **Platform** | [Daytona.io](https://www.daytona.io/) — Cloud sandbox |
| **Size** | Daytona Large (2 CPU / 4 GB RAM / 8 GB Disk) |
| **Auto-Stop** | 43,800 minutes (~30 days) |
| **Public Preview** | ✅ HTTP preview enabled |
| **Cost** | 💰 Free |
| **OS** | Ubuntu (Linux) |

---

## 📋 Step-by-Step Guide

### Step 1 — Create a Daytona Account

1. Go to 👉 [https://www.daytona.io/](https://www.daytona.io/)
2. Click **"Sign Up"**
3. Choose your sign-in method:
   - 📧 **Email**
   - 🟢 **Google (Gmail)**
   - ⚫ **GitHub**
4. Complete registration & verify your email

---

### Step 2 — Create a Sandbox

1. Navigate to **Sandboxes** (or click **"Create Sandbox"**)
2. Fill in the following:

| Setting | Value |
|---------|-------|
| **Name** | `my-free-vps` *(or anything you like)* |
| **Sandbox Class** | `daytona-vm-large` |
| **Auto-Stop Interval** | `43800` *(minutes ≈ 30 days)* |
| **Public HTTP Preview** | ✅ **Checked / Enabled** |

3. Click **Create**
4. Wait a few seconds for the sandbox to provision

> ⚠️ **Note:** `43800` minutes = 730 hours ≈ **30.4 days** of idle time before auto-stop.

---

### Step 3 — Open the Terminal

1. Once the sandbox is **Running**, click on it
2. Click the **Terminal** tab (or the terminal icon)
3. You now have a full Linux shell

---

### Step 4 — Run the Setup Script

Paste this single command into the terminal:

```bash
curl -sL https://raw.githubusercontent.com/SomratChandraRoy/cc-toolkit/main/setup.sh | bash   

```


### IF ANY ERROR  go error.md file 
