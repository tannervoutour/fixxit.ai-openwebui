# Production Deployment Plan - app.fixxit.ai

This document outlines the complete plan for deploying the production environment of Fixxit.ai OpenWebUI.

---

## 🚀 TL;DR - Quick Summary

**Good News**: Most infrastructure is already set up!

**What's Already Done**:
- ✅ DNS: app.fixxit.ai points to server
- ✅ Reverse Proxy: Caddy configured and running
- ✅ SSL: Auto-managed by Caddy (Let's Encrypt)
- ✅ Ports: 8081 and 5174 are available

**What You Need to Do**:
1. Copy `/home/ec2-user/fixxit.ai-openwebui` → `/home/ec2-user/fixxit.ai-openwebui-prod`
2. Update ports in `start_server.sh` (8080→8081, 5173→5174)
3. Start production server
4. Test that app.fixxit.ai works

**Estimated Time**: ~30 minutes

**Risk Level**: Low (dev environment stays untouched, easy rollback)

---

## Overview

**Goal**: Copy the working dev environment to a separate production directory and configure DNS for app.fixxit.ai to point to it.

**Current State**:
- Dev Environment: `/home/ec2-user/fixxit.ai-openwebui` (dev.fixxit.ai, ports 8080/5173)
- Production: Not yet deployed

**Target State**:
- Dev Environment: `/home/ec2-user/fixxit.ai-openwebui` (dev.fixxit.ai, ports 8080/5173)
- Production Environment: `/home/ec2-user/fixxit.ai-openwebui-prod` (app.fixxit.ai, ports 8081/5174)

---

## Phase 1: Directory Copy Strategy

### Research: Best Practices for Directory Copying

**Options for Copying**:

1. **rsync (Recommended)**
   - Preserves permissions, timestamps, symlinks
   - Can exclude unnecessary files
   - Fast and reliable
   - Command:
   ```bash
   rsync -av --exclude='logs/*' --exclude='*.pyc' --exclude='__pycache__' \
         --exclude='node_modules' --exclude='.git' \
         /home/ec2-user/fixxit.ai-openwebui/ \
         /home/ec2-user/fixxit.ai-openwebui-prod/
   ```

2. **cp -a (Alternative)**
   - Archive mode preserves everything
   - Simpler but less control
   - Command:
   ```bash
   cp -a /home/ec2-user/fixxit.ai-openwebui /home/ec2-user/fixxit.ai-openwebui-prod
   ```

3. **tar + extract (For exact replica)**
   - Creates exact copy including hidden files
   - Good for verification
   - Commands:
   ```bash
   cd /home/ec2-user
   tar czf openwebui-backup.tar.gz fixxit.ai-openwebui/
   mkdir fixxit.ai-openwebui-prod
   tar xzf openwebui-backup.tar.gz -C fixxit.ai-openwebui-prod --strip-components=1
   ```

**Recommended Approach**: Use `rsync` with exclusions

### Files/Directories to Exclude

- `logs/*` - Start fresh logs for production
- `*.pyc` and `__pycache__/` - Python bytecode (will regenerate)
- `node_modules/` - Will reinstall for production
- `.git/` - Don't need git history in production
- `backend/data/webui.db` - Need to decide: copy or start fresh?

### Critical Files to Preserve

✅ **MUST Copy**:
- `backend/.env` - Contains encryption key
- `backend/open_webui/` - All Python code
- `src/` - All frontend code
- `start_server.sh` - Server management script
- `package.json` and `package-lock.json` - Frontend dependencies
- `vite.config.ts` - Frontend build configuration

⚠️ **Decide**:
- `backend/data/webui.db` - Production should probably start with a copy of dev DB or fresh?
- `backend/venv/` - Can copy or rebuild (rebuild is cleaner)

---

## Phase 2: Production Configuration Changes

### 2.1 Port Configuration

**Backend Port**: Change from 8080 to 8081
**Frontend Port**: Change from 5173 to 5174

**Files to Modify**:

1. **`start_server.sh`**
   ```bash
   # BEFORE (dev)
   BACKEND_PORT=8080
   FRONTEND_PORT=5173

   # AFTER (production)
   BACKEND_PORT=8081
   FRONTEND_PORT=5174
   ```

2. **`.env` or Environment Variables**
   ```bash
   # Add production-specific environment variables
   WEBUI_URL=https://app.fixxit.ai
   FRONTEND_BASE_URL=https://app.fixxit.ai
   ```

3. **Frontend API Base URL** (if hardcoded anywhere)
   - Check `src/lib/apis/` for any hardcoded backend URLs
   - Should use relative paths or environment variables

### 2.2 Database Configuration

**Decision Required**:
- **Option A**: Copy dev database to production (keeps all users, groups, invitations)
- **Option B**: Start with fresh database (clean slate for production)

**Recommendation**: Copy dev database, then clean out test data if needed

**Commands**:
```bash
# Copy database
cp /home/ec2-user/fixxit.ai-openwebui/backend/data/webui.db \
   /home/ec2-user/fixxit.ai-openwebui-prod/backend/data/webui.db

# Set proper permissions
chmod 644 /home/ec2-user/fixxit.ai-openwebui-prod/backend/data/webui.db
```

### 2.3 Encryption Key (CRITICAL)

⚠️ **MUST use the same encryption key in production**

The key MUST be identical:
```bash
DATABASE_PASSWORD_ENCRYPTION_KEY="ajZEaDE4QmUwQmlsRzVjVjBSWnJSamxTOXRXdGhYWVF1U2l4T3VQMkRLND0="
```

This goes in:
- `/home/ec2-user/fixxit.ai-openwebui-prod/backend/.env`
- `/home/ec2-user/fixxit.ai-openwebui-prod/start_server.sh`

### 2.4 Log Directory

Create fresh log directory:
```bash
mkdir -p /home/ec2-user/fixxit.ai-openwebui-prod/logs
chmod 755 /home/ec2-user/fixxit.ai-openwebui-prod/logs
```

### 2.5 Virtual Environment

**Option A**: Copy existing venv (faster)
```bash
rsync -av /home/ec2-user/fixxit.ai-openwebui/backend/venv/ \
          /home/ec2-user/fixxit.ai-openwebui-prod/backend/venv/
```

**Option B**: Rebuild venv (cleaner, recommended)
```bash
cd /home/ec2-user/fixxit.ai-openwebui-prod/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.6 Frontend Dependencies

Reinstall node_modules for production:
```bash
cd /home/ec2-user/fixxit.ai-openwebui-prod
npm install --production
```

---

## Phase 3: DNS and Reverse Proxy Configuration

### 3.1 Current DNS Setup ✅ CONFIRMED

**Current Configuration**:
- ✅ **Reverse Proxy**: Caddy (not nginx/Apache)
- ✅ **Caddy Status**: Running and active
- ✅ **SSL Certificates**: Auto-managed by Caddy (Let's Encrypt)
- ✅ **Ports**: 80 (HTTP redirect) and 443 (HTTPS) handled by Caddy
- ✅ **Production Config**: Already exists for app.fixxit.ai → port 8081
- ✅ **Available Ports**: 8081 and 5174 are available

**Caddy Configuration File**: `/etc/caddy/Caddyfile`

**Existing Configuration for app.fixxit.ai**:
```caddy
app.fixxit.ai {
    # Automatic HTTPS with Let's Encrypt

    # Reverse proxy to backend
    reverse_proxy localhost:8081 {
        # WebSocket support
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}

        # Health check
        health_uri /health
        health_interval 30s
        health_timeout 5s
    }

    # Security headers (HSTS, XSS protection, etc.)
    # Compression (gzip, zstd)
    # Logging to /var/log/caddy/app.fixxit.ai.log
}
```

**IMPORTANT FINDING**: The production configuration is already complete! Caddy is already configured to proxy app.fixxit.ai to localhost:8081. We just need to start the production server on port 8081.

### 3.2 DNS and SSL Configuration ✅ ALREADY CONFIGURED

**Good News**: DNS and SSL are already fully configured!

**Current Setup**:
- ✅ DNS A record for app.fixxit.ai already points to the server (18.204.97.97)
- ✅ Caddy configuration for app.fixxit.ai already exists
- ✅ SSL certificate will be automatically generated by Caddy when production starts
- ✅ No manual DNS or SSL configuration needed

**How Caddy Works**:
1. When the production server starts on port 8081, Caddy detects traffic to app.fixxit.ai
2. Caddy automatically requests SSL certificate from Let's Encrypt
3. Caddy handles all HTTP → HTTPS redirects automatically
4. Caddy proxies all requests from app.fixxit.ai to localhost:8081
5. Certificate auto-renewal is built-in (no cron jobs needed)

**What You Need to Do**: Nothing! Just start the production server.

### 3.3 Verifying Caddy Configuration

To verify the Caddy configuration is working:

```bash
# Check Caddy status
systemctl status caddy

# View Caddy logs
journalctl -u caddy -f

# Test Caddy configuration (if changes needed)
caddy validate --config /etc/caddy/Caddyfile

# Reload Caddy (if Caddyfile is modified)
sudo systemctl reload caddy
```

---

## Phase 4: Deployment Steps (DO NOT EXECUTE YET)

### Step-by-Step Deployment Process

#### Step 1: Stop dev server (optional, for safety)
```bash
ssh -i ~/.ssh/lightsail-key.pem ec2-user@18.204.97.97
cd /home/ec2-user/fixxit.ai-openwebui
./start_server.sh stop
```

#### Step 2: Copy directory structure
```bash
# On server
cd /home/ec2-user

# Use rsync to copy everything
rsync -av --exclude='logs/*' --exclude='*.pyc' --exclude='__pycache__' \
      --exclude='node_modules' --exclude='.git' \
      fixxit.ai-openwebui/ fixxit.ai-openwebui-prod/

# Verify copy
ls -la fixxit.ai-openwebui-prod/
```

#### Step 3: Update production configuration
```bash
cd /home/ec2-user/fixxit.ai-openwebui-prod

# Update start_server.sh - change ports to 8081/5174
sed -i 's/BACKEND_PORT=8080/BACKEND_PORT=8081/g' start_server.sh
sed -i 's/FRONTEND_PORT=5173/FRONTEND_PORT=5174/g' start_server.sh

# Verify changes
grep -E 'BACKEND_PORT|FRONTEND_PORT' start_server.sh
```

#### Step 4: Setup production environment
```bash
cd /home/ec2-user/fixxit.ai-openwebui-prod

# Create fresh logs directory
mkdir -p logs
chmod 755 logs

# Rebuild Python venv (recommended for clean install)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Install frontend dependencies
cd /home/ec2-user/fixxit.ai-openwebui-prod
npm install --production
```

#### Step 5: Verify encryption key
```bash
# Check that .env has the correct encryption key
cat /home/ec2-user/fixxit.ai-openwebui-prod/backend/.env | grep DATABASE_PASSWORD_ENCRYPTION_KEY

# Should output:
# DATABASE_PASSWORD_ENCRYPTION_KEY=ajZEaDE4QmUwQmlsRzVjVjBSWnJSamxTOXRXdGhYWVF1U2l4T3VQMkRLND0=
```

#### Step 6: Copy or initialize database
```bash
# Option A: Copy dev database
cp /home/ec2-user/fixxit.ai-openwebui/backend/data/webui.db \
   /home/ec2-user/fixxit.ai-openwebui-prod/backend/data/webui.db

# Option B: Let it initialize fresh
# (Just start the server and it will create new DB)
```

#### Step 7: Start production server
```bash
cd /home/ec2-user/fixxit.ai-openwebui-prod
./start_server.sh start

# Check status
./start_server.sh status

# Check logs
tail -f logs/backend.log
```

#### Step 8: Verify production is running locally
```bash
# Test backend
curl http://localhost:8081/api/version

# Test frontend (from browser or curl)
curl http://localhost:5174
```

#### Step 9: Verify Caddy is handling requests
```bash
# Caddy should automatically detect and proxy app.fixxit.ai
# Check Caddy logs to verify
journalctl -u caddy -f

# In another terminal, test the connection
curl https://app.fixxit.ai/api/version

# Caddy will automatically generate SSL certificate on first request
# This may take a few seconds
```

#### Step 10: Verify SSL Certificate
```bash
# Check SSL certificate was generated
echo | openssl s_client -servername app.fixxit.ai -connect app.fixxit.ai:443 2>/dev/null | openssl x509 -noout -dates

# Should show certificate dates from Let's Encrypt
```

#### Step 11: Restart dev environment
```bash
cd /home/ec2-user/fixxit.ai-openwebui
./start_server.sh start
```

#### Step 12: Verify both environments
```bash
# Dev should be running
curl https://dev.fixxit.ai/api/version

# Production should be running
curl https://app.fixxit.ai/api/version
```

---

## Phase 5: Testing Checklist

After deployment, verify all functionality on app.fixxit.ai:

### Authentication & Users
- [ ] Can register new user
- [ ] Can login with existing user
- [ ] Admin dashboard loads
- [ ] User Management tab works
- [ ] Manager dashboard loads (for manager users)

### Groups & Permissions
- [ ] Can view managed groups
- [ ] Can see group members
- [ ] Managers can only see their groups
- [ ] Admins can see all groups

### Invitations
- [ ] Can create new invitation
- [ ] Invitation URL shows "app.fixxit.ai" (not dev.fixxit.ai)
- [ ] Invitation link works when clicked
- [ ] Can revoke invitation
- [ ] Can delete invitation

### Logs
- [ ] Logs page loads
- [ ] Logs display consistently (no random failures)
- [ ] No "Failed to decrypt password" errors in backend logs
- [ ] Can filter logs
- [ ] Can search logs

### Chat Functionality
- [ ] Can create new chat
- [ ] Can send messages
- [ ] Can view chat history
- [ ] Models load correctly

---

## Phase 6: Rollback Plan

If production deployment fails:

### Quick Rollback
```bash
# Stop production server
cd /home/ec2-user/fixxit.ai-openwebui-prod
./start_server.sh stop

# Update DNS to point back to dev (if changed)
# Or remove nginx config for app.fixxit.ai
sudo rm /etc/nginx/conf.d/app.fixxit.ai.conf
sudo systemctl reload nginx

# Ensure dev is running
cd /home/ec2-user/fixxit.ai-openwebui
./start_server.sh start
```

### Clean Up Failed Production
```bash
# Remove production directory
rm -rf /home/ec2-user/fixxit.ai-openwebui-prod

# Remove SSL certificate if created
sudo certbot delete --cert-name app.fixxit.ai
```

---

## Phase 7: Post-Deployment Maintenance

### Monitoring Production
```bash
# Watch production logs
ssh -i ~/.ssh/lightsail-key.pem ec2-user@18.204.97.97
tail -f /home/ec2-user/fixxit.ai-openwebui-prod/logs/backend.log

# Check process status
ps aux | grep -E "uvicorn|node" | grep -v grep

# Check port usage
netstat -tlnp | grep -E ':(8080|8081|5173|5174)'
```

### Future Updates
When updating code:
1. Update dev environment first
2. Test thoroughly on dev.fixxit.ai
3. If successful, update production:
   ```bash
   # Copy changed files from dev to prod
   rsync -av --exclude='logs/*' --exclude='*.pyc' \
         /home/ec2-user/fixxit.ai-openwebui/backend/open_webui/ \
         /home/ec2-user/fixxit.ai-openwebui-prod/backend/open_webui/

   # Restart production
   cd /home/ec2-user/fixxit.ai-openwebui-prod
   ./start_server.sh restart
   ```

### Backup Strategy
```bash
# Weekly database backup
cp /home/ec2-user/fixxit.ai-openwebui-prod/backend/data/webui.db \
   /home/ec2-user/backups/webui-$(date +%Y%m%d).db

# Keep last 30 days
find /home/ec2-user/backups/ -name "webui-*.db" -mtime +30 -delete
```

---

## Key Decisions Required Before Deployment

✅ **RESOLVED**:
- ✅ **Reverse Proxy**: Caddy is already configured
- ✅ **SSL Certificate**: Caddy auto-generates via Let's Encrypt
- ✅ **Port Configuration**: Ports 8081/5174 are available
- ✅ **DNS**: app.fixxit.ai already points to the server

⚠️ **STILL NEED TO DECIDE**:
1. **Database Strategy**: Copy dev DB or start fresh?
   - **Recommendation**: Copy dev DB to preserve users, groups, and configurations
   - **Alternative**: Start fresh if you want production to be clean

2. **Frontend Build**: Should production use built/minified frontend or dev server?
   - **Current**: Dev is using Vite dev server (port 5173)
   - **Recommendation**: Use dev server for now, optimize later with `npm run build`
   - **Note**: Built version would be faster but requires different deployment setup

---

## Next Steps

1. **Research current server setup**:
   - Check for existing reverse proxy (nginx/Apache)
   - Verify DNS configuration for dev.fixxit.ai
   - Check SSL certificate setup
   - Verify available ports

2. **Make decisions** on database and SSL strategy

3. **Test directory copy** process on a test directory first

4. **Execute deployment** following steps in Phase 4

5. **Run full testing checklist** from Phase 5

6. **Monitor production** for first 24 hours closely

---

## Critical Warnings

⚠️ **DO NOT change the encryption key** - Must be identical to dev
⚠️ **DO NOT forget to update ports** in start_server.sh
⚠️ **DO NOT skip SSL certificate** configuration
⚠️ **DO NOT deploy without testing** the copy process first
⚠️ **DO backup the database** before any production deployment
