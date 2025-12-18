# Fixxit.ai OpenWebUI - Production Deployment Guide

**Version:** 1.0
**Last Updated:** December 18, 2025
**For:** Production server deployment of Fixxit.ai OpenWebUI with Supabase logs integration

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Initial Server Setup](#initial-server-setup)
4. [Automated Setup](#automated-setup)
5. [Manual Setup](#manual-setup)
6. [Environment Configuration](#environment-configuration)
7. [Starting the Server](#starting-the-server)
8. [Verification & Health Checks](#verification--health-checks)
9. [Supabase Integration Setup](#supabase-integration-setup)
10. [Reverse Proxy Configuration](#reverse-proxy-configuration)
11. [Security Hardening](#security-hardening)
12. [Monitoring & Maintenance](#monitoring--maintenance)
13. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying to production, ensure you have:

- [ ] Linux server (Ubuntu 22.04 LTS or similar recommended)
- [ ] Root or sudo access
- [ ] Domain name pointing to your server (optional but recommended)
- [ ] Supabase project(s) set up for logs storage
- [ ] OpenAI API key (for AI-enhanced logs)
- [ ] SSH access to the server

---

## System Requirements

### Minimum Requirements

- **CPU:** 2 cores
- **RAM:** 4GB
- **Storage:** 20GB free space
- **Network:** Static IP or domain name
- **OS:** Ubuntu 22.04 LTS, Debian 12, or similar

### Recommended Requirements

- **CPU:** 4+ cores
- **RAM:** 8GB+
- **Storage:** 50GB+ SSD
- **Network:** High-speed connection
- **OS:** Ubuntu 22.04 LTS

### Software Dependencies

- **Python:** 3.11 or higher
- **Node.js:** 18.x or 22.x (LTS versions)
- **npm:** 8.x or higher
- **Git:** 2.x or higher

---

## Initial Server Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Required System Packages

```bash
sudo apt install -y \
  build-essential \
  curl \
  git \
  python3 \
  python3-pip \
  python3-venv \
  libpq-dev \
  postgresql-client \
  nginx \
  certbot \
  python3-certbot-nginx
```

### 3. Install Node.js via nvm (Recommended)

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Reload shell
source ~/.bashrc

# Install Node.js LTS
nvm install 22
nvm use 22
nvm alias default 22
```

### 4. Create Application User (Recommended)

```bash
# Create dedicated user for security
sudo adduser --disabled-password --gecos "" openwebui
sudo usermod -aG sudo openwebui

# Switch to application user
sudo su - openwebui
```

---

## Automated Setup

We provide an automated setup script for quick deployment.

### Quick Start (Recommended)

```bash
# Clone repository
git clone https://github.com/tannervoutour/fixxit.ai-openwebui.git
cd fixxit.ai-openwebui

# Checkout production branch
git checkout fixxit-main

# Run automated setup
./setup_production.sh
```

The script will:
- ✅ Check system dependencies
- ✅ Install Python dependencies
- ✅ Install Node.js dependencies
- ✅ Build production frontend
- ✅ Create necessary directories
- ✅ Generate encryption keys
- ✅ Set up systemd service (optional)
- ✅ Configure basic security

**Follow the prompts** and the script will guide you through configuration.

---

## Manual Setup

If you prefer manual setup or the automated script fails:

### 1. Clone Repository

```bash
git clone https://github.com/tannervoutour/fixxit.ai-openwebui.git
cd fixxit.ai-openwebui
git checkout fixxit-main
```

### 2. Set Up Python Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

cd ..
```

### 3. Set Up Frontend

```bash
# Install Node.js dependencies
npm install

# Build production frontend
npm run build
```

### 4. Create Required Directories

```bash
mkdir -p logs
mkdir -p backend/data
chmod 755 logs backend/data
```

---

## Environment Configuration

### 1. Create Production Environment File

```bash
cp .env.production.template .env
```

### 2. Configure Critical Environment Variables

Edit `.env` with your production values:

```bash
nano .env
```

**Required Variables:**

```bash
# Database Encryption (CRITICAL - Generate new key!)
DATABASE_PASSWORD_ENCRYPTION_KEY="<generate-with-setup-script>"

# Server Configuration
HOST="0.0.0.0"
PORT="8080"
WEBUI_URL="https://your-domain.com"

# OpenAI API (Required for AI logs)
OPENAI_API_KEY="sk-..."

# Security
WEBUI_SECRET_KEY="<generate-random-string>"

# Production Settings
ENV="production"
DEBUG_MODE="false"
```

**Generate Encryption Key:**

```bash
python3 -c "from cryptography.fernet import Fernet; import base64; key = Fernet.generate_key(); print(base64.urlsafe_b64encode(key).decode())"
```

### 3. Set Appropriate Permissions

```bash
chmod 600 .env
```

---

## Starting the Server

### Option 1: Direct Start (Testing)

```bash
# Activate Python environment
cd backend
source venv/bin/activate

# Start server
./start.sh
```

Server will be available at `http://localhost:8080`

### Option 2: Using Management Script (Recommended)

```bash
# From project root
./start_server.sh start
```

**Available Commands:**
- `./start_server.sh start` - Start server
- `./start_server.sh stop` - Stop server
- `./start_server.sh restart` - Restart server
- `./start_server.sh status` - Check status
- `./start_server.sh logs` - View logs

### Option 3: Systemd Service (Production)

Create service file:

```bash
sudo nano /etc/systemd/system/openwebui.service
```

```ini
[Unit]
Description=Fixxit.ai OpenWebUI Server
After=network.target

[Service]
Type=simple
User=openwebui
WorkingDirectory=/home/openwebui/fixxit.ai-openwebui/backend
Environment="PATH=/home/openwebui/fixxit.ai-openwebui/backend/venv/bin"
EnvironmentFile=/home/openwebui/fixxit.ai-openwebui/.env
ExecStart=/home/openwebui/fixxit.ai-openwebui/backend/venv/bin/python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable openwebui
sudo systemctl start openwebui
sudo systemctl status openwebui
```

---

## Verification & Health Checks

### 1. Run Health Check Script

```bash
./health_check.sh
```

This will verify:
- ✅ Server is responding
- ✅ Database is accessible
- ✅ API endpoints are working
- ✅ Frontend is loading
- ✅ Supabase connections (if configured)

### 2. Manual Health Check

```bash
# Check server is running
curl http://localhost:8080/health

# Expected response: {"status":"ok"}
```

### 3. Check Logs

```bash
# View application logs
tail -f logs/backend.log

# View systemd logs (if using systemd)
sudo journalctl -u openwebui -f
```

---

## Supabase Integration Setup

### 1. Prepare Supabase Database

For each group that needs logs, create a Supabase project:

1. Go to https://supabase.com
2. Create a new project
3. Note the connection details

### 2. Create Logs Table

In your Supabase SQL Editor:

```sql
CREATE TABLE logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id TEXT NOT NULL,
    user_name TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT,
    priority TEXT,
    tags TEXT[],
    metadata JSONB,
    ai_summary TEXT,
    ai_insights TEXT[],
    ai_tags TEXT[],
    ticket_number TEXT,
    status TEXT DEFAULT 'open',
    assigned_to TEXT,
    resolution_notes TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    attachments JSONB,
    related_logs TEXT[],
    visible_to_groups TEXT[] DEFAULT ARRAY[]::TEXT[],
    search_vector TSVECTOR
);

-- Create indexes for performance
CREATE INDEX idx_logs_user_id ON logs(user_id);
CREATE INDEX idx_logs_created_at ON logs(created_at DESC);
CREATE INDEX idx_logs_category ON logs(category);
CREATE INDEX idx_logs_status ON logs(status);
CREATE INDEX idx_logs_search ON logs USING GIN(search_vector);
CREATE INDEX idx_logs_tags ON logs USING GIN(tags);

-- Create search trigger
CREATE TRIGGER logs_search_update
BEFORE INSERT OR UPDATE ON logs
FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.english', title, content);
```

### 3. Generate Encryption Key

```bash
export DATABASE_PASSWORD_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; import base64; key = Fernet.generate_key(); print(base64.urlsafe_b64encode(key).decode())")

echo "Add this to your .env file:"
echo "DATABASE_PASSWORD_ENCRYPTION_KEY=\"$DATABASE_PASSWORD_ENCRYPTION_KEY\""
```

### 4. Configure Groups in OpenWebUI

After server starts:

1. Login as admin
2. Go to **Admin Panel → Users → Groups**
3. Create or edit a group
4. Go to **Database** tab
5. Enter Supabase connection string:
   ```
   psql -h db.xxx.supabase.co -p 5432 -d postgres -U postgres
   ```
6. Enter database password
7. Click **Test Connection**
8. Save if successful

---

## Reverse Proxy Configuration

### Nginx Configuration (Recommended)

Create Nginx config:

```bash
sudo nano /etc/nginx/sites-available/openwebui
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration (will be added by certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Increase upload size for file uploads
    client_max_body_size 100M;
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/openwebui /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Certificate with Let's Encrypt

```bash
sudo certbot --nginx -d your-domain.com
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

### 2. Fail2Ban (Optional but Recommended)

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Secure Environment Files

```bash
chmod 600 .env
chmod 600 .env.production.local
```

### 4. Regular Updates

```bash
# Create update script
cat > update.sh << 'EOF'
#!/bin/bash
git pull origin fixxit-main
source backend/venv/bin/activate
pip install -r backend/requirements.txt
npm install
npm run build
sudo systemctl restart openwebui
EOF

chmod +x update.sh
```

---

## Monitoring & Maintenance

### Log Rotation

Create log rotation config:

```bash
sudo nano /etc/logrotate.d/openwebui
```

```
/home/openwebui/fixxit.ai-openwebui/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 openwebui openwebui
    sharedscripts
    postrotate
        systemctl reload openwebui > /dev/null 2>&1 || true
    endscript
}
```

### Monitoring Script

```bash
# Add to crontab
crontab -e

# Check health every 5 minutes
*/5 * * * * /home/openwebui/fixxit.ai-openwebui/health_check.sh >> /home/openwebui/health_check.log 2>&1
```

### Backup Strategy

```bash
# Backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/openwebui"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
tar -czf $BACKUP_DIR/data_$DATE.tar.gz backend/data/

# Backup environment
cp .env $BACKUP_DIR/env_$DATE

# Keep last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "env_*" -mtime +7 -delete
EOF

chmod +x backup.sh

# Run daily at 2 AM
echo "0 2 * * * /home/openwebui/fixxit.ai-openwebui/backup.sh" | crontab -
```

---

## Troubleshooting

### Server Won't Start

```bash
# Check Python environment
source backend/venv/bin/activate
python --version

# Check dependencies
pip list | grep -i fastapi

# Check port availability
sudo netstat -tlnp | grep 8080

# Check logs
tail -f logs/backend.log
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity
psql -h db.xxx.supabase.co -p 5432 -d postgres -U postgres

# Check encryption key
env | grep DATABASE_PASSWORD_ENCRYPTION_KEY
```

### Frontend Not Loading

```bash
# Rebuild frontend
npm run build

# Check built files
ls -la build/
```

### High Memory Usage

```bash
# Reduce workers in systemd service
# Edit: ExecStart=... --workers 2

# Restart service
sudo systemctl restart openwebui
```

### Permission Errors

```bash
# Fix permissions
sudo chown -R openwebui:openwebui /home/openwebui/fixxit.ai-openwebui
chmod -R 755 /home/openwebui/fixxit.ai-openwebui
chmod 600 .env
```

---

## Support & Resources

- **Documentation:** See `FIXXIT_SETUP.md` for development setup
- **Quick Start:** See `QUICKSTART.md` for rapid deployment
- **Health Checks:** Run `./health_check.sh` for diagnostics
- **GitHub:** https://github.com/tannervoutour/fixxit.ai-openwebui
- **Upstream OpenWebUI:** https://docs.openwebui.com

---

## Deployment Checklist

Before going live, verify:

- [ ] Server meets minimum requirements
- [ ] All dependencies installed
- [ ] `.env` configured with production values
- [ ] `DATABASE_PASSWORD_ENCRYPTION_KEY` set
- [ ] Frontend built successfully
- [ ] Backend starts without errors
- [ ] Health check passes
- [ ] Supabase databases configured
- [ ] Groups configured with database connections
- [ ] Reverse proxy configured (nginx)
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Systemd service enabled
- [ ] Log rotation configured
- [ ] Backup strategy implemented
- [ ] Monitoring in place

---

**Deployment Date:** _______________
**Deployed By:** _______________
**Server:** _______________
**Domain:** _______________
