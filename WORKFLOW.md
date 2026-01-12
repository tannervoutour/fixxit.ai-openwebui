# Development & Deployment Workflow

## 📋 Overview

This guide explains the systematic workflow for developing, building, and deploying your customized OpenWebUI.

---

## 🔄 The Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  LOCAL DEVELOPMENT                                          │
│  - Edit code in WSL                                        │
│  - Test with ./start_dev.sh                               │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  DEPLOYMENT SCRIPT (./deploy-full.sh)                      │
│  1. Commit & push to GitHub (source code only)            │
│  2. Build frontend locally (avoid server memory issues)    │
│  3. Server pulls from GitHub (backend code)                │
│  4. Transfer built frontend to server                      │
│  5. Restart backend                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  PRODUCTION SERVER (Lightsail)                             │
│  - Backend code from GitHub                                │
│  - Built frontend from local machine                       │
│  - Serving at http://98.92.94.174:8080                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Daily Development Workflow

### **Standard Full Deployment** (Most Common)

When you've made changes and want to deploy everything:

```bash
./deploy-full.sh
```

This interactive script will:
1. ✅ Show your changes
2. ✅ Ask for commit message
3. ✅ Push to GitHub
4. ✅ Build frontend locally
5. ✅ Sync server with GitHub
6. ✅ Deploy frontend
7. ✅ Restart backend

### **Quick Deployment with Message**

Skip the prompt by providing a commit message:

```bash
./deploy-full.sh --message "Add new feature X"
# or short form:
./deploy-full.sh -m "Fix bug in logs modal"
```

### **Dry Run** (Test Without Changes)

See what would happen without actually doing it:

```bash
./deploy-full.sh --dry-run
```

---

## 🎯 Selective Deployment Scenarios

### **Frontend Only Changes**

If you only changed frontend code (no backend changes to sync):

```bash
./deploy-full.sh --skip-sync
```

This skips the server git pull step.

### **Backend Only Changes**

If you only changed backend code (no frontend rebuild needed):

```bash
./deploy-full.sh --skip-build
```

Uses existing build directory.

### **Already Committed to Git**

If you already committed/pushed manually:

```bash
./deploy-full.sh --skip-git
```

Skips commit/push, just builds and deploys.

### **Deploy Without Restart**

If backend is already running and you don't want to restart:

```bash
./deploy-full.sh --no-restart
```

---

## 📦 Individual Script Usage

### **`./deploy-full.sh`** - Complete Workflow (Recommended)

The all-in-one solution:
- Handles git, build, sync, and deploy
- Interactive or automated
- Best for regular deployments

```bash
# Full deployment (interactive)
./deploy-full.sh

# With commit message (automated)
./deploy-full.sh -m "Update UI"

# Dry run
./deploy-full.sh --dry-run
```

### **`./deploy-to-lightsail.sh`** - Frontend Only

Use when you want fine control over just frontend deployment:

```bash
# Deploy existing build
./deploy-to-lightsail.sh --skip-build --restart

# Build and deploy
./deploy-to-lightsail.sh --restart
```

### **`./start_dev.sh`** - Local Development

For local development with hot module reloading:

```bash
# Start development servers
./start_dev.sh start

# Frontend: http://localhost:5173
# Backend: http://localhost:8080
```

---

## 🗂️ What Goes Where?

### **Git Repository (GitHub)**

```
✅ Backend source code (backend/)
✅ Frontend source code (src/)
✅ Configuration files (.env.example, package.json, etc.)
✅ Scripts (deploy-full.sh, start_server.sh, etc.)
❌ Build directory (build/) - in .gitignore
❌ node_modules/ - in .gitignore
❌ Environment secrets (.env, .deploy-config) - in .gitignore
```

### **Local Machine (WSL)**

```
✅ Full git repository
✅ node_modules/ (for building)
✅ build/ (generated by npm run build)
✅ .deploy-config (your deployment secrets)
```

### **Production Server (Lightsail)**

```
✅ Git repository (pulled from GitHub)
✅ Backend Python environment (venv/)
✅ build/ (deployed from local machine)
❌ node_modules/ - NOT needed on server!
```

---

## 🔧 Common Scenarios

### **Scenario 1: Made UI Changes**

```bash
# Make changes to src/lib/components/...
# Test locally
./start_dev.sh start

# When ready to deploy
./deploy-full.sh -m "Improve logs modal UI"
```

### **Scenario 2: Made Backend Changes**

```bash
# Make changes to backend/open_webui/...
# Test locally
./start_dev.sh start

# Deploy (can skip frontend build if no UI changes)
./deploy-full.sh -m "Add new API endpoint" --skip-build
```

### **Scenario 3: Made Both Frontend & Backend Changes**

```bash
# Make changes everywhere
# Test locally
./start_dev.sh start

# Full deployment
./deploy-full.sh -m "Add complete feature X"
```

### **Scenario 4: Quick Hotfix**

```bash
# Fix critical bug
# Test locally

# Quick deploy with short message
./deploy-full.sh -m "hotfix: fix critical login bug"
```

### **Scenario 5: Experimenting (Not Ready to Deploy)**

```bash
# Just keep working locally
./start_dev.sh start

# No deployment needed
# Git commits are optional during experimentation
```

---

## 🔍 Verification After Deployment

### **Check Deployment Status**

```bash
# SSH to server
ssh -i ~/.ssh/lightsail-key.pem ec2-user@98.92.94.174

# Check server status
cd fixxit.ai-openwebui
./start_server.sh status

# Check backend logs
tail -f logs/backend.log

# Exit
exit
```

### **Test in Browser**

Visit: **http://98.92.94.174:8080**

### **Verify Git Sync**

```bash
# Check local and remote are in sync
git status
git log --oneline -5

# On server (via SSH)
cd fixxit.ai-openwebui
git log --oneline -5
```

---

## ⚙️ Configuration Files

### **`.deploy-config`** (Never commit!)

Contains server credentials:
```bash
DEPLOY_HOST="98.92.94.174"
DEPLOY_USER="ec2-user"
DEPLOY_PORT="22"
DEPLOY_KEY="$HOME/.ssh/lightsail-key.pem"
DEPLOY_REMOTE_PATH="/home/ec2-user/fixxit.ai-openwebui"
```

### **`.env`** (Never commit!)

Contains environment secrets:
```bash
DATABASE_PASSWORD_ENCRYPTION_KEY="your-key-here"
OPENAI_API_KEY="your-key-here"
# etc...
```

Both are already in `.gitignore` for safety.

---

## 🐛 Troubleshooting

### **Build Fails Locally**

```bash
# Clean and rebuild
rm -rf node_modules .svelte-kit build
npm install --legacy-peer-deps
npm run build
```

### **Git Push Fails**

```bash
# Check remote
git remote -v

# Pull first if behind
git pull origin fixxit-main
git push origin fixxit-main
```

### **Server Sync Fails**

```bash
# SSH manually and check
ssh -i ~/.ssh/lightsail-key.pem ec2-user@98.92.94.174
cd fixxit.ai-openwebui
git status
git pull origin main  # or your branch
```

### **Deployment Takes Forever**

```bash
# Check if rsync is installed (should be faster)
which rsync

# On server
ssh to-server
which rsync

# Install if missing
sudo yum install rsync
```

### **Backend Won't Start**

```bash
# SSH to server
ssh -i ~/.ssh/lightsail-key.pem ec2-user@98.92.94.174
cd fixxit.ai-openwebui

# Check logs
tail -50 logs/backend.log

# Try manual restart
./start_server.sh stop
./start_server.sh start
```

---

## 📊 Deployment Comparison

| Scenario | Command | Git | Build | Sync | Deploy | Restart |
|----------|---------|-----|-------|------|--------|---------|
| **Full deployment** | `./deploy-full.sh` | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Quick commit** | `./deploy-full.sh -m "msg"` | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Frontend only** | `./deploy-full.sh --skip-sync` | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Backend only** | `./deploy-full.sh --skip-build` | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Already committed** | `./deploy-full.sh --skip-git` | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Test run** | `./deploy-full.sh --dry-run` | 🔍 | 🔍 | 🔍 | 🔍 | 🔍 |

---

## 💡 Best Practices

1. **Test Locally First** - Always run `./start_dev.sh` before deploying
2. **Commit Often** - Small, focused commits are easier to track
3. **Use Meaningful Messages** - Future you will thank you
4. **Dry Run on Big Changes** - Use `--dry-run` for major updates
5. **Check Server Logs** - After deployment, verify everything works
6. **Keep Secrets Safe** - Never commit `.env` or `.deploy-config`
7. **Pull Before Push** - Keep local repo synced with GitHub

---

## 🎓 Understanding the Architecture

### **Why Build Locally?**

Your Lightsail instance has limited memory. Building the frontend requires significant RAM and causes crashes. By building on your local WSL environment (with plenty of memory), you avoid this issue entirely.

### **Why Not Commit Built Files?**

The `build/` directory is:
- **Large** (188MB+)
- **Generated** (can be recreated from source)
- **Environment-specific** (may have hardcoded paths)
- **Changes every build** (makes git history messy)

Instead, we:
- Commit source code to git
- Build locally when deploying
- Transfer only the built files to the server

This matches how the official `open-webui` package works!

### **The Two-Track System**

```
TRACK 1 (Source Code):
  Local → GitHub → Server
  [git push]      [git pull]

TRACK 2 (Built Frontend):
  Local → Server
  [rsync/scp]
```

Backend and frontend source travel via git.
Built frontend travels directly via rsync.

---

## 📚 Quick Reference

```bash
# Most common command (full deployment)
./deploy-full.sh -m "your commit message"

# Local development
./start_dev.sh start

# Manual frontend-only deploy
./deploy-to-lightsail.sh --restart

# Check what would happen
./deploy-full.sh --dry-run

# SSH to server
ssh -i ~/.ssh/lightsail-key.pem ec2-user@98.92.94.174
```

---

**Last Updated:** 2025-12-27
**Your Server:** http://98.92.94.174:8080
**Git Branch:** fixxit-main
