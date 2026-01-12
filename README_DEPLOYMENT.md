# 🚀 Fixxit.ai OpenWebUI - Deployment System

> **Your complete systematic workflow for development and production deployment**

---

## 📖 Quick Start

```bash
# 1. Make your changes to the code
# 2. Test locally (optional but recommended)
./start_dev.sh start

# 3. Deploy everything with one command
./deploy-full.sh -m "description of your changes"

# Done! Your changes are live at http://98.92.94.174:8080
```

---

## 🎯 What This System Does

This deployment system solves the **Lightsail memory problem** by:

1. ✅ **Building frontend locally** (no server crashes)
2. ✅ **Committing source to GitHub** (version control)
3. ✅ **Syncing server with GitHub** (backend updates)
4. ✅ **Deploying built frontend** (fast rsync transfer)
5. ✅ **Restarting backend** (picks up all changes)

**Result:** Professional one-command deployment without memory issues!

---

## 📁 Documentation Structure

| File | Purpose | When to Use |
|------|---------|-------------|
| **CHEATSHEET.md** | Quick command reference | Quick lookup during work |
| **WORKFLOW.md** | Complete workflow guide | Understanding the system |
| **DEPLOYMENT.md** | Technical deployment details | Troubleshooting, advanced use |
| **DEPLOY_QUICKSTART.md** | Fast start guide | First-time setup |
| **README_DEPLOYMENT.md** | This file - overview | Starting point |

---

## 🔧 Available Scripts

### **`./deploy-full.sh`** ⭐ RECOMMENDED

**The complete deployment solution**

```bash
# Interactive (prompts for commit message)
./deploy-full.sh

# Automated (provide commit message)
./deploy-full.sh -m "your changes"

# Test without making changes
./deploy-full.sh --dry-run
```

**What it does:**
1. Commits & pushes to GitHub
2. Builds frontend locally
3. Syncs server with GitHub
4. Deploys frontend to server
5. Restarts backend

### **`./deploy-to-lightsail.sh`**

**Frontend-only deployment** (when you need fine control)

```bash
# Build and deploy
./deploy-to-lightsail.sh --restart

# Deploy existing build
./deploy-to-lightsail.sh --skip-build --restart
```

### **`./start_dev.sh`**

**Local development with hot reload**

```bash
./start_dev.sh start
# Frontend: http://localhost:5173
# Backend: http://localhost:8080
```

### **`./start_server.sh`**

**Server management** (use on Lightsail)

```bash
./start_server.sh start    # Start backend
./start_server.sh stop     # Stop backend
./start_server.sh status   # Check status
./start_server.sh restart  # Restart backend
```

---

## 🎨 Typical Development Flow

### Daily Work
```bash
# Morning: Start development environment
./start_dev.sh start

# Work on features, make changes
# Test in browser: http://localhost:5173

# Afternoon: Deploy to production
./deploy-full.sh -m "Add feature X and fix bug Y"

# Evening: Verify deployment
curl http://98.92.94.174:8080/health
```

### Quick Hotfix
```bash
# Fix the bug
nano src/lib/components/SomeComponent.svelte

# Deploy immediately
./deploy-full.sh -m "hotfix: fix critical bug"
```

### Feature Branch Workflow
```bash
# Create feature branch
git checkout -b feature/new-logs-view

# Make changes, test locally
./start_dev.sh start

# Deploy to production
./deploy-full.sh -m "Add new logs view"

# Merge to main if needed
git checkout fixxit-main
git merge feature/new-logs-view
git push origin fixxit-main
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR LOCAL MACHINE (WSL)                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Source Code (Git Repo)                            │   │
│  │  • Backend (Python)                                │   │
│  │  • Frontend (Svelte/TypeScript)                    │   │
│  │  • Configuration                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                        │                                    │
│         ┌──────────────┴──────────────┐                    │
│         │                             │                    │
│         ▼                             ▼                    │
│  ┌─────────────┐             ┌─────────────┐              │
│  │ Git Push    │             │ npm build   │              │
│  │ (source)    │             │ (frontend)  │              │
│  └──────┬──────┘             └──────┬──────┘              │
└─────────│─────────────────────────────│─────────────────────┘
          │                             │
          │                             │ rsync
          │ git pull                    │
          │                             │
          ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│  LIGHTSAIL SERVER                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Backend (from Git)                                │   │
│  │  • Python venv                                     │   │
│  │  • FastAPI server                                  │   │
│  │  • SQLite database                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Frontend (from local build)                       │   │
│  │  • Static files in /build                          │   │
│  │  • Served by backend                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Serves: http://98.92.94.174:8080                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 💡 Key Concepts

### **Why Build Locally?**

Lightsail has limited memory. Building the frontend (187MB of assets) requires significant RAM and causes crashes. Your local WSL environment has plenty of memory.

### **What Goes in Git?**

✅ **Commit:**
- Backend source code
- Frontend source code
- Configuration templates
- Scripts

❌ **Don't commit:**
- `build/` directory (generated files)
- `node_modules/` (too large)
- `.env` (secrets)
- `.deploy-config` (credentials)

### **The Two-Track System**

**Track 1: Source Code**
```
Local (git push) → GitHub → Server (git pull)
```

**Track 2: Built Frontend**
```
Local (npm build + rsync) → Server
```

This separation keeps git clean while ensuring the server has everything it needs.

---

## 🔐 Security

### Configuration Files (Never Commit!)

**`.deploy-config`** - Deployment credentials
```bash
DEPLOY_HOST="98.92.94.174"
DEPLOY_USER="ec2-user"
DEPLOY_KEY="$HOME/.ssh/lightsail-key.pem"
DEPLOY_REMOTE_PATH="/home/ec2-user/fixxit.ai-openwebui"
```

**`.env`** - Application secrets
```bash
DATABASE_PASSWORD_ENCRYPTION_KEY="..."
OPENAI_API_KEY="..."
```

Both are in `.gitignore` for protection.

### SSH Key

Location: `~/.ssh/lightsail-key.pem`
```bash
# Verify permissions
ls -lah ~/.ssh/lightsail-key.pem
# Should show: -r-------- (400)
```

---

## 🐛 Common Issues & Solutions

### "Build fails with out of memory"
**This shouldn't happen anymore!** You're building locally now.

### "Permission denied (publickey)"
```bash
# Check SSH key exists and has correct permissions
ls -lah ~/.ssh/lightsail-key.pem
chmod 400 ~/.ssh/lightsail-key.pem

# Test SSH connection
ssh -i ~/.ssh/lightsail-key.pem ec2-user@98.92.94.174
```

### "Git push rejected"
```bash
# Pull first, then push
git pull origin fixxit-main
git push origin fixxit-main
```

### "Backend won't start on server"
```bash
# SSH to server
ssh -i ~/.ssh/lightsail-key.pem ec2-user@98.92.94.174
cd fixxit.ai-openwebui

# Check logs
tail -50 logs/backend.log

# Restart
./start_server.sh restart
```

### "npm run build fails"
```bash
# Clean rebuild
rm -rf node_modules .svelte-kit build
npm install --legacy-peer-deps
npm run build
```

---

## 📊 Deployment Options

| Option | Use Case |
|--------|----------|
| `./deploy-full.sh -m "msg"` | Standard deployment (most common) |
| `./deploy-full.sh --skip-git` | Already committed manually |
| `./deploy-full.sh --skip-build` | Backend changes only |
| `./deploy-full.sh --skip-sync` | Frontend changes only |
| `./deploy-full.sh --no-restart` | Don't restart backend |
| `./deploy-full.sh --dry-run` | Test without making changes |

---

## ✅ Verification Checklist

After deployment:

- [ ] Git pushed successfully
- [ ] Build completed without errors
- [ ] Server synced with GitHub
- [ ] Frontend deployed
- [ ] Backend restarted
- [ ] Website accessible at http://98.92.94.174:8080
- [ ] No errors in backend logs
- [ ] Features work as expected

```bash
# Quick verification command
ssh -i ~/.ssh/lightsail-key.pem ec2-user@98.92.94.174 \
  "cd fixxit.ai-openwebui && ./start_server.sh status && tail -20 logs/backend.log"
```

---

## 🎓 Learning Resources

1. **Start here:** `CHEATSHEET.md` - Quick command reference
2. **Understand the workflow:** `WORKFLOW.md` - Complete guide
3. **Deep dive:** `DEPLOYMENT.md` - Technical details
4. **Troubleshooting:** Check the Common Issues section above

---

## 🚦 Status Check

### Current Configuration
- **Server:** 98.92.94.174:8080
- **Branch:** fixxit-main
- **Build Method:** Local (avoids server memory issues)
- **Deployment:** Automated via `deploy-full.sh`

### System Health
```bash
# Check everything
./deploy-full.sh --dry-run

# Test SSH
ssh -i ~/.ssh/lightsail-key.pem ec2-user@98.92.94.174 "echo OK"

# Check server
ssh -i ~/.ssh/lightsail-key.pem ec2-user@98.92.94.174 \
  "cd fixxit.ai-openwebui && ./start_server.sh status"
```

---

## 🎉 You're All Set!

Your deployment system is now **production-ready** and **systematic**:

✅ **No more memory crashes** - Build locally
✅ **Version controlled** - Git integration
✅ **One-command deployment** - Automated workflow
✅ **Fully documented** - Multiple guides
✅ **Secure** - Credentials protected

**Start deploying:**
```bash
./deploy-full.sh -m "your first systematic deployment"
```

---

**Questions?** Check `WORKFLOW.md` for detailed explanations or `CHEATSHEET.md` for quick answers.

**Last Updated:** 2025-12-27
**System Version:** 1.0.0
