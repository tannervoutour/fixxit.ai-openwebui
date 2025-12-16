# Fixxit.ai OpenWebUI - Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Development Workflow](#development-workflow)
3. [Production Deployment](#production-deployment)
4. [Server Setup](#server-setup)
5. [Deployment Process](#deployment-process)
6. [Updating the Application](#updating-the-application)
7. [Troubleshooting](#troubleshooting)
8. [Backup and Recovery](#backup-and-recovery)

---

## Overview

This guide covers the complete workflow for developing and deploying Fixxit.ai OpenWebUI:

- **Local Development**: Native Python/Node.js with hot-reload for fast iteration
- **Production Deployment**: Docker containers for consistent, reliable deployment
- **CI/CD Ready**: Scripts for automated builds and deployments

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Development (Local)                       │
├─────────────────────────────────────────────────────────────┤
│  ✓ Native Python + Node.js                                  │
│  ✓ Hot module replacement (instant updates)                 │
│  ✓ ./start_dev.sh start                                     │
│  ✓ Backend: http://127.0.0.1:8080                          │
│  ✓ Frontend: http://localhost:5173                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ git push
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   GitHub Repository                          │
├─────────────────────────────────────────────────────────────┤
│  ✓ Source code version control                              │
│  ✓ Branch: fixxit-main                                      │
│  ✓ Commit history                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ git pull + ./deploy-docker.sh pull
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Production Server (Docker)                   │
├─────────────────────────────────────────────────────────────┤
│  ✓ Docker container                                          │
│  ✓ Production-optimized build                                │
│  ✓ http://your-server:3000                                  │
│  ✓ Persistent data volumes                                   │
│  ✓ Auto-restart on failure                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Development Workflow

### 1. Start Local Development

**Use the native development server for daily work:**

```bash
# Start development servers with hot-reload
./start_dev.sh start

# Access the application
# - Frontend: http://localhost:5173 (with HMR)
# - Backend: http://127.0.0.1:8080 (with auto-reload)
```

### 2. Make Changes

Edit files in `src/` (frontend) or `backend/` (backend):
- Svelte components update instantly in browser
- Python code reloads automatically
- Database schema changes require migration

### 3. Test Changes Locally

```bash
# Check server status
./start_dev.sh status

# View logs
./start_dev.sh logs

# Restart if needed
./start_dev.sh restart
```

### 4. Commit Changes

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: your feature description"

# Push to GitHub
git push origin fixxit-main
```

---

## Production Deployment

### Prerequisites

**On your production server:**
- Docker Engine 20.10+
- Docker Compose V2
- Git
- 4GB+ RAM recommended
- 20GB+ disk space

**Install Docker on Ubuntu/Debian:**
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Verify installation
docker --version
docker compose version
```

---

## Server Setup

### 1. Clone Repository on Server

```bash
# SSH into your production server
ssh user@your-server.com

# Clone the repository
git clone https://github.com/your-username/fixxit-openwebui.git
cd fixxit-openwebui

# Checkout production branch
git checkout fixxit-main
```

### 2. Configure Environment

```bash
# Copy production environment template
cp .env.production .env.production.local

# Edit with your production settings
nano .env.production.local
```

**Critical settings to configure:**

```bash
# Basic Configuration
WEBUI_NAME=Fixxit.ai
WEBUI_URL=https://fixxit.yourdomain.com
WEBUI_PORT=3000

# CRITICAL: Generate strong secrets
WEBUI_SECRET_KEY=$(openssl rand -hex 32)

# CRITICAL: Database password encryption (must match development!)
DATABASE_PASSWORD_ENCRYPTION_KEY=aEtZV05XcVpuTG03VUNUczc5dlMtalY4WEdleDZheHY0Z0NuZ1I1SnZtaz0=

# Data storage location
DATA_VOLUME_PATH=/opt/fixxit-openwebui/data

# AI API Keys
OPENAI_API_KEY=your-actual-openai-key
ANTHROPIC_API_KEY=your-actual-anthropic-key
```

### 3. Create Data Directory

```bash
# Create data directory for persistent storage
sudo mkdir -p /opt/fixxit-openwebui/data
sudo chown -R $USER:$USER /opt/fixxit-openwebui

# Or let the deploy script create it
# It will prompt you automatically
```

### 4. Initial Deployment

```bash
# Make scripts executable (if not already)
chmod +x build-docker.sh deploy-docker.sh

# Build Docker image
./build-docker.sh

# Deploy to production
./deploy-docker.sh deploy
```

---

## Deployment Process

### Method 1: Deploy from Local Build (Recommended for First Deploy)

**On your local machine:**

```bash
# 1. Build Docker image locally
./build-docker.sh v1.0.0

# 2. Save image to file
docker save fixxit-openwebui:v1.0.0 | gzip > fixxit-openwebui-v1.0.0.tar.gz

# 3. Transfer to server
scp fixxit-openwebui-v1.0.0.tar.gz user@your-server:/tmp/
```

**On your production server:**

```bash
# 1. Load Docker image
docker load < /tmp/fixxit-openwebui-v1.0.0.tar.gz

# 2. Deploy
cd /path/to/fixxit-openwebui
./deploy-docker.sh deploy v1.0.0

# 3. Verify deployment
./deploy-docker.sh status
```

### Method 2: Pull and Build on Server (For Updates)

**On your production server:**

```bash
# This will:
# 1. Pull latest code from GitHub
# 2. Build new Docker image
# 3. Ask if you want to deploy immediately
./deploy-docker.sh pull
```

### Method 3: Manual Build on Server

**On your production server:**

```bash
# 1. Pull latest code
git pull origin fixxit-main

# 2. Build image
./build-docker.sh $(git rev-parse --short HEAD)

# 3. Deploy
./deploy-docker.sh deploy $(git rev-parse --short HEAD)
```

---

## Updating the Application

### Standard Update Workflow

**1. Make changes locally and test:**
```bash
# On local machine
./start_dev.sh start
# ... make your changes ...
# ... test thoroughly ...
```

**2. Commit and push:**
```bash
git add .
git commit -m "feat: your new feature"
git push origin fixxit-main
```

**3. Deploy to production:**
```bash
# SSH to server
ssh user@your-server.com
cd /path/to/fixxit-openwebui

# Pull and rebuild (easiest method)
./deploy-docker.sh pull
```

### Quick Deploy Script

Create this script on your server for even faster deploys:

```bash
#!/bin/bash
# File: /usr/local/bin/fixxit-update
cd /path/to/fixxit-openwebui
git pull origin fixxit-main
./build-docker.sh $(git rev-parse --short HEAD)
./deploy-docker.sh deploy $(git rev-parse --short HEAD)
```

Then just run: `fixxit-update`

---

## Deployment Commands Reference

### Build Commands

```bash
# Build with auto-generated timestamp tag
./build-docker.sh

# Build with specific version
./build-docker.sh v1.0.0

# Build with git commit hash
./build-docker.sh $(git rev-parse --short HEAD)

# Build and tag as latest
./build-docker.sh latest
```

### Deploy Commands

```bash
# Deploy latest version
./deploy-docker.sh deploy

# Deploy specific version
./deploy-docker.sh deploy v1.0.0

# Pull from GitHub and rebuild
./deploy-docker.sh pull

# Check deployment status
./deploy-docker.sh status

# View logs
./deploy-docker.sh logs

# Restart containers
./deploy-docker.sh restart

# Stop containers
./deploy-docker.sh stop

# Backup data
./deploy-docker.sh backup
```

### Docker Compose Commands

```bash
# View running containers
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart service
docker compose -f docker-compose.prod.yml restart

# Stop services
docker compose -f docker-compose.prod.yml down

# Start services
docker compose -f docker-compose.prod.yml up -d

# Pull new images
docker compose -f docker-compose.prod.yml pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
./deploy-docker.sh logs

# Check container status
docker ps -a

# Inspect container
docker inspect fixxit-openwebui

# Check environment variables
docker exec fixxit-openwebui env
```

### Database Issues

```bash
# Access container shell
docker exec -it fixxit-openwebui bash

# Check database file
ls -lh /app/backend/data/webui.db

# View database location
echo $DATABASE_URL
```

### Port Already in Use

```bash
# Find what's using port 3000
sudo lsof -i :3000
sudo netstat -tulpn | grep 3000

# Change port in .env.production.local
WEBUI_PORT=3001
```

### Supabase Connection Issues

```bash
# Verify encryption key is set
docker exec fixxit-openwebui env | grep DATABASE_PASSWORD_ENCRYPTION_KEY

# Test database connection from container
docker exec -it fixxit-openwebui bash
python -c "import asyncpg; print('asyncpg installed')"
```

### Out of Disk Space

```bash
# Check disk usage
df -h

# Clean up old images
docker image prune -a

# Clean up old containers
docker container prune

# Clean up volumes (CAREFUL!)
docker volume prune  # Don't delete fixxit_openwebui_data!
```

### Memory Issues

```bash
# Check container memory usage
docker stats fixxit-openwebui

# Increase memory limit in docker-compose.prod.yml
# Under deploy.resources.limits.memory: 4G -> 8G
```

---

## Backup and Recovery

### Manual Backup

```bash
# Using deployment script (recommended)
./deploy-docker.sh backup

# Manual backup
tar -czf fixxit-backup-$(date +%Y%m%d).tar.gz /opt/fixxit-openwebui/data
```

### Automated Backups

**Create cron job:**

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/fixxit-openwebui && ./deploy-docker.sh backup

# Add weekly backup and upload to S3 (example)
0 3 * * 0 cd /path/to/fixxit-openwebui && ./deploy-docker.sh backup && aws s3 cp backups/$(ls -t backups/ | head -1) s3://your-bucket/
```

### Restore from Backup

```bash
# Stop container
./deploy-docker.sh stop

# Restore data
tar -xzf fixxit-backup-YYYYMMDD.tar.gz -C /opt/fixxit-openwebui/

# Start container
./deploy-docker.sh deploy
```

### Export/Import Docker Image

```bash
# Export image
docker save fixxit-openwebui:latest | gzip > fixxit-image.tar.gz

# Import on another server
docker load < fixxit-image.tar.gz
```

---

## Production Checklist

### Before First Deployment

- [ ] Server meets minimum requirements (4GB RAM, 20GB disk)
- [ ] Docker and Docker Compose installed
- [ ] Repository cloned to server
- [ ] `.env.production.local` configured with strong secrets
- [ ] `DATABASE_PASSWORD_ENCRYPTION_KEY` matches development
- [ ] Data directory created and has correct permissions
- [ ] Firewall rules configured (port 3000 open)
- [ ] Domain name configured (if using)
- [ ] SSL certificate set up (if using HTTPS)

### After Deployment

- [ ] Application accessible at configured URL
- [ ] Health check passing (`./deploy-docker.sh status`)
- [ ] Can log in with admin account
- [ ] Supabase logs integration working
- [ ] File uploads working
- [ ] AI models responding correctly
- [ ] Backup cron job configured
- [ ] Monitoring configured (optional)

### Regular Maintenance

- [ ] Weekly: Check disk space and logs
- [ ] Monthly: Test backup restoration
- [ ] Quarterly: Update base images and dependencies
- [ ] As needed: Apply security patches
- [ ] Always: Monitor application performance

---

## Security Best Practices

1. **Never commit** `.env.production.local` to git
2. **Use strong secrets** generated with `openssl rand -hex 32`
3. **Keep encryption key secure** - losing it means losing access to group database passwords
4. **Set up firewall** rules to restrict access
5. **Use HTTPS** in production with valid SSL certificates
6. **Regular updates** of base images and dependencies
7. **Backup regularly** and test restoration procedures
8. **Monitor logs** for suspicious activity
9. **Limit SSH access** to production server
10. **Use non-root user** for Docker operations

---

## Quick Reference

### Local Development
```bash
./start_dev.sh start     # Start development servers
./start_dev.sh stop      # Stop servers
./start_dev.sh logs      # View logs
```

### Build for Production
```bash
./build-docker.sh v1.0.0     # Build image
```

### Deploy to Production
```bash
./deploy-docker.sh pull      # Pull from GitHub and deploy
./deploy-docker.sh deploy    # Deploy existing image
./deploy-docker.sh status    # Check status
./deploy-docker.sh logs      # View logs
./deploy-docker.sh backup    # Create backup
```

### Emergency Commands
```bash
./deploy-docker.sh stop      # Stop everything
./deploy-docker.sh restart   # Quick restart
docker logs fixxit-openwebui # View raw logs
```

---

## Support

For issues or questions:
1. Check logs: `./deploy-docker.sh logs`
2. Check status: `./deploy-docker.sh status`
3. Review CLAUDE_KEEPUP.md for implementation details
4. Check GitHub issues: https://github.com/your-repo/issues

---

**Last Updated**: December 2025
**Version**: 1.0
**Maintainer**: Fixxit.ai Team
