# Fixxit.ai OpenWebUI - Quick Deployment Guide

This is a condensed version of the full DEPLOYMENT.md guide. Use this for quick reference.

---

## 🚀 Quick Start: Local Development

```bash
# Start development (hot-reload)
./start_dev.sh start

# Access at:
# - Frontend: http://localhost:5173
# - Backend: http://127.0.0.1:8080

# Make changes, test, commit
git add .
git commit -m "feat: your feature"
git push origin fixxit-main
```

---

## 🐳 Quick Start: Production Deployment

### First-Time Server Setup

**1. Install Docker on server:**
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

**2. Clone repo:**
```bash
git clone https://github.com/your-username/fixxit-openwebui.git
cd fixxit-openwebui
git checkout fixxit-main
```

**3. Configure environment:**
```bash
cp .env.production .env.production.local
nano .env.production.local  # Edit with your settings
```

**4. Deploy:**
```bash
./build-docker.sh
./deploy-docker.sh deploy
```

---

## 🔄 Updating Production

### Method 1: Pull and Rebuild (Easiest)

**On your production server:**
```bash
cd /path/to/fixxit-openwebui
./deploy-docker.sh pull
```

This will:
1. Pull latest code from GitHub
2. Build new Docker image
3. Ask if you want to deploy

### Method 2: Manual Update

```bash
git pull origin fixxit-main
./build-docker.sh $(git rev-parse --short HEAD)
./deploy-docker.sh deploy $(git rev-parse --short HEAD)
```

---

## 📋 Common Commands

### Local Development
```bash
./start_dev.sh start      # Start dev servers
./start_dev.sh stop       # Stop servers
./start_dev.sh restart    # Restart servers
./start_dev.sh logs       # View logs
./start_dev.sh status     # Check status
```

### Production Deployment
```bash
./build-docker.sh                    # Build image
./deploy-docker.sh deploy            # Deploy latest
./deploy-docker.sh pull              # Pull from GitHub & rebuild
./deploy-docker.sh status            # Check deployment status
./deploy-docker.sh logs              # View container logs
./deploy-docker.sh restart           # Restart container
./deploy-docker.sh stop              # Stop container
./deploy-docker.sh backup            # Backup data
```

---

## 🛠️ Typical Workflow

### Development → Production

```bash
# 1. LOCAL: Make changes and test
./start_dev.sh start
# ... edit code ...
# ... test thoroughly ...

# 2. LOCAL: Commit and push
git add .
git commit -m "feat: new feature"
git push origin fixxit-main

# 3. SERVER: Update production
ssh user@your-server.com
cd /path/to/fixxit-openwebui
./deploy-docker.sh pull
# Confirm deployment when prompted
```

---

## 🔥 Troubleshooting

### Check Logs
```bash
# Production
./deploy-docker.sh logs

# Development
./start_dev.sh logs
```

### Check Status
```bash
# Production
./deploy-docker.sh status
docker ps

# Development
./start_dev.sh status
```

### Container Won't Start
```bash
# View detailed logs
docker logs fixxit-openwebui

# Check environment
docker exec fixxit-openwebui env

# Restart from scratch
./deploy-docker.sh stop
./deploy-docker.sh deploy
```

### Port Already in Use
```bash
# Find what's using port
sudo lsof -i :3000

# Change port in .env.production.local
WEBUI_PORT=3001
```

---

## 💾 Backups

### Create Backup
```bash
./deploy-docker.sh backup
```

### Restore Backup
```bash
./deploy-docker.sh stop
tar -xzf backups/fixxit-backup-YYYYMMDD-HHMMSS.tar.gz -C /opt/fixxit-openwebui/
./deploy-docker.sh deploy
```

### Automated Daily Backups
```bash
# Add to crontab
crontab -e

# Add this line (daily at 2 AM)
0 2 * * * cd /path/to/fixxit-openwebui && ./deploy-docker.sh backup
```

---

## ⚙️ Critical Environment Variables

**In `.env.production.local`:**

```bash
# REQUIRED: Strong secrets
WEBUI_SECRET_KEY=$(openssl rand -hex 32)

# CRITICAL: Must match development if migrating data
DATABASE_PASSWORD_ENCRYPTION_KEY=aEtZV05XcVpuTG03VUNUczc5dlMtalY4WEdleDZheHY0Z0NuZ1I1SnZtaz0=

# Your settings
WEBUI_NAME=Fixxit.ai
WEBUI_URL=https://fixxit.yourdomain.com
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Data location
DATA_VOLUME_PATH=/opt/fixxit-openwebui/data
```

---

## 📞 Need Help?

1. **Check logs**: `./deploy-docker.sh logs`
2. **Check status**: `./deploy-docker.sh status`
3. **Read full guide**: See `DEPLOYMENT.md`
4. **Check implementation**: See `CLAUDE_KEEPUP.md`

---

## ✅ Pre-Deployment Checklist

**Before first production deployment:**

- [ ] Docker installed on server
- [ ] Repository cloned
- [ ] `.env.production.local` configured
- [ ] Strong `WEBUI_SECRET_KEY` generated
- [ ] `DATABASE_PASSWORD_ENCRYPTION_KEY` set (use same as dev!)
- [ ] Data directory created: `/opt/fixxit-openwebui/data`
- [ ] Firewall port 3000 open
- [ ] Domain/SSL configured (if applicable)

**After deployment:**

- [ ] Application accessible
- [ ] Can log in
- [ ] Supabase logs working
- [ ] File uploads working
- [ ] Backup cron job set up

---

**Quick Reference Complete** ✅

For detailed information, see `DEPLOYMENT.md`
