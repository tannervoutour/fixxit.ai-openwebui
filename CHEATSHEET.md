# Deployment Cheat Sheet

## 🚀 Most Common Commands

```bash
# Full deployment (interactive - prompts for commit message)
./deploy-full.sh

# Full deployment with message (automated)
./deploy-full.sh -m "your commit message here"

# Test what would happen (dry run)
./deploy-full.sh --dry-run

# Local development with hot reload
./start_dev.sh start
```

---

## 📋 Quick Workflows

### Standard Deployment Flow
```bash
# 1. Make your changes
# 2. Test locally
./start_dev.sh start

# 3. Deploy everything
./deploy-full.sh -m "description of changes"

# Done! 🎉
```

### Frontend Only
```bash
# Changed UI only, no backend changes
./deploy-full.sh -m "UI updates" --skip-sync
```

### Backend Only
```bash
# Changed backend only, no UI rebuild needed
./deploy-full.sh -m "API updates" --skip-build
```

### Already Committed to Git
```bash
# If you already did git commit/push manually
./deploy-full.sh --skip-git
```

---

## 🔧 All Options for deploy-full.sh

```bash
--message "msg"   # or -m "msg" - Git commit message
--skip-git        # Skip git commit/push
--skip-build      # Skip frontend build (use existing)
--skip-sync       # Skip server git pull
--no-restart      # Don't restart backend
--dry-run         # Show what would be done
--help            # Show help
```

---

## 🔍 Verification Commands

```bash
# Check local git status
git status
git log --oneline -5

# SSH to server
ssh -i ~/.ssh/lightsail-key.pem ec2-user@98.92.94.174

# On server - check status
cd fixxit.ai-openwebui
./start_server.sh status
tail -f logs/backend.log

# Check if server synced with git
git log --oneline -5
```

---

## 🌐 Access Points

- **Production**: http://98.92.94.174:8080
- **Local Frontend**: http://localhost:5173 (dev mode)
- **Local Backend**: http://localhost:8080 (dev mode)

---

## 🐛 Quick Fixes

### Build Fails
```bash
rm -rf node_modules .svelte-kit build
npm install --legacy-peer-deps
npm run build
```

### Server Won't Start
```bash
ssh -i ~/.ssh/lightsail-key.pem ec2-user@98.92.94.174
cd fixxit.ai-openwebui
./start_server.sh stop
./start_server.sh start
tail -f logs/backend.log
```

### Git Conflicts
```bash
git pull origin fixxit-main
# Resolve conflicts
git add .
git commit -m "Merge conflicts resolved"
git push origin fixxit-main
```

---

## 📁 File Locations

- **Deployment config**: `.deploy-config` (never commit!)
- **Environment secrets**: `.env` (never commit!)
- **SSH key**: `~/.ssh/lightsail-key.pem`
- **Build output**: `build/` (generated, not in git)

---

## ⚡ Pro Tips

```bash
# Alias for quick deploy (add to ~/.bashrc)
alias deploy='./deploy-full.sh -m'

# Usage:
deploy "quick fix"

# Create git alias for your branch
git config alias.pushf 'push origin fixxit-main'

# Quick commit and push
git add . && git commit -m "update" && git pushf
```

---

## 🎯 Decision Tree

```
Did you change code?
├─ Yes → What changed?
│  ├─ Frontend only → ./deploy-full.sh -m "msg" --skip-sync
│  ├─ Backend only  → ./deploy-full.sh -m "msg" --skip-build
│  └─ Both          → ./deploy-full.sh -m "msg"
└─ No → Nothing to deploy!
```

---

## 🔐 Security

**Never commit these files:**
- `.env`
- `.deploy-config`
- `~/.ssh/lightsail-key.pem`

**Already protected by `.gitignore`:**
- ✅ `.env`
- ✅ `.deploy-config`
- ✅ `build/`
- ✅ `node_modules/`

---

## 📞 Help

```bash
# Show full help
./deploy-full.sh --help

# Check deployment config
cat .deploy-config

# Test SSH connection
ssh -i ~/.ssh/lightsail-key.pem ec2-user@98.92.94.174 "echo Connection successful"
```

---

**Quick Reference Docs:**
- Full workflow: `WORKFLOW.md`
- Deployment details: `DEPLOYMENT.md`
- Quick start: `DEPLOY_QUICKSTART.md`
