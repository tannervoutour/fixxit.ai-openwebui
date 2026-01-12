# Quick Start: Deploy to Lightsail

## 🚀 TL;DR

```bash
# 1. Setup (first time only)
cp .deploy-config.example .deploy-config
nano .deploy-config  # Add your Lightsail details

# 2. Deploy
./deploy-to-lightsail.sh --restart

# Done! Your frontend is deployed 🎉
```

---

## Why This Approach?

Your Lightsail instance **doesn't have enough memory** to build the frontend. Solution: Build locally, deploy the pre-built files.

This mimics how the official `open-webui` package works - it ships with pre-built frontend assets in the Python wheel.

---

## First Time Setup (5 minutes)

### 1. Create deployment config

```bash
cp .deploy-config.example .deploy-config
nano .deploy-config
```

### 2. Fill in your Lightsail details:

```bash
DEPLOY_HOST="18.XXX.XXX.XXX"           # Your Lightsail IP
DEPLOY_USER="ubuntu"                    # Usually 'ubuntu'
DEPLOY_KEY="~/.ssh/YourKey.pem"        # Your Lightsail SSH key
DEPLOY_REMOTE_PATH="/home/ubuntu/fixxit_projectFiles/fixxitUI_OpenWebUI"
```

### 3. Set SSH key permissions

```bash
chmod 400 ~/.ssh/YourLightsailKey.pem
```

### 4. Test connection

```bash
ssh -i ~/.ssh/YourLightsailKey.pem ubuntu@your-lightsail-ip
exit
```

**Done!** You're ready to deploy.

---

## Deploying Updates

Every time you make frontend changes:

```bash
./deploy-to-lightsail.sh --restart
```

This will:
1. ✅ Build frontend locally (2-3 minutes)
2. ✅ Transfer to Lightsail (30 seconds - 2 minutes)
3. ✅ Restart backend

---

## Common Commands

```bash
# Full deployment with backend restart
./deploy-to-lightsail.sh --restart

# Deploy without restart (if backend already running)
./deploy-to-lightsail.sh

# Test what will happen (no changes made)
./deploy-to-lightsail.sh --dry-run

# Redeploy existing build (skip build step)
./deploy-to-lightsail.sh --skip-build --restart

# Show all options
./deploy-to-lightsail.sh --help
```

---

## What About the Backend?

The backend **doesn't need to be rebuilt or redeployed** when you change frontend code.

Backend changes are deployed separately (git pull on the server, restart backend).

This script is **only for frontend deployment**.

---

## Troubleshooting

### Error: "SSH connection failed"

1. Check Lightsail firewall allows SSH from your IP
2. Verify key path: `ls -lah ~/.ssh/YourKey.pem`
3. Test manual SSH: `ssh -i ~/.ssh/YourKey.pem ubuntu@your-ip`

### Error: "Frontend build failed"

```bash
# Clean and rebuild
rm -rf node_modules .svelte-kit
npm install --legacy-peer-deps
npm run build
```

### Deployment is slow

Install rsync on both machines for 5-10x faster transfers:

```bash
# Local
sudo apt install rsync

# On Lightsail
ssh to-server
sudo apt install rsync
```

### How do I verify deployment worked?

```bash
# SSH to server
ssh -i ~/.ssh/key.pem ubuntu@your-ip

# Check if backend sees the build
cd /path/to/project
ls -lah build/

# Check backend logs
tail -f logs/backend.log

# Or check systemd logs
sudo journalctl -u openwebui -f
```

Then visit your Lightsail IP in a browser.

---

## Full Documentation

For more details, see [DEPLOYMENT.md](./DEPLOYMENT.md)

---

**Need help?** Check the troubleshooting section in DEPLOYMENT.md or review the deployment logs.
