# Frontend Deployment Guide

## Overview

This project uses a **local build + remote deploy** strategy to avoid memory issues when building the large frontend directly on AWS Lightsail.

**How it works:**
1. Build the frontend on your local machine (which has enough memory)
2. Transfer only the built static files to the Lightsail server
3. Backend serves the pre-built files (no build needed on server)

This mirrors how the official `open-webui` Python package works - it includes pre-built frontend assets so users never have to build them.

---

## Initial Setup

### 1. Install Dependencies Locally

Make sure you have Node.js 18+ and npm installed on your local machine:

```bash
node --version  # Should be 18+
npm --version   # Should be 6+
```

### 2. Configure Deployment Settings

Copy the example config and edit it with your Lightsail details:

```bash
cp .deploy-config.example .deploy-config
nano .deploy-config
```

Fill in your Lightsail instance details:
```bash
DEPLOY_HOST="your-instance.amazonaws.com"  # Your Lightsail IP or hostname
DEPLOY_USER="ubuntu"                        # SSH username
DEPLOY_PORT="22"                            # SSH port
DEPLOY_KEY="~/.ssh/YourKey.pem"            # Path to your Lightsail SSH key
DEPLOY_REMOTE_PATH="/home/ubuntu/path"     # Where OpenWebUI is installed
```

### 3. Set SSH Key Permissions

```bash
chmod 400 ~/.ssh/YourLightsailKey.pem
```

### 4. Test SSH Connection

Verify you can connect to your server:

```bash
ssh -i ~/.ssh/YourLightsailKey.pem ubuntu@your-instance.amazonaws.com
```

---

## Deploying the Frontend

### Basic Deployment

Build locally and deploy to server:

```bash
./deploy-to-lightsail.sh
```

This will:
1. ✅ Check dependencies (Node.js, npm, ssh, rsync)
2. ✅ Test SSH connection
3. ✅ Build frontend locally (`npm run build`)
4. ✅ Transfer files to Lightsail (using rsync or scp)
5. ✅ Show deployment summary

### Deployment with Backend Restart

Deploy and automatically restart the backend:

```bash
./deploy-to-lightsail.sh --restart
```

### Skip Build (Use Existing Build)

If you've already built locally and just want to re-deploy:

```bash
./deploy-to-lightsail.sh --skip-build
```

### Dry Run (See What Would Happen)

Test the deployment process without making changes:

```bash
./deploy-to-lightsail.sh --dry-run
```

---

## Advanced Options

### Command-Line Override

You can override config file settings via command-line:

```bash
./deploy-to-lightsail.sh \
  --host 123.456.789.10 \
  --user ubuntu \
  --key ~/.ssh/different-key.pem \
  --remote-path /home/ubuntu/project \
  --restart
```

### All Available Options

```bash
./deploy-to-lightsail.sh --help
```

Options:
- `--host <hostname>` - Override deploy host
- `--user <username>` - Override SSH user
- `--port <port>` - Override SSH port (default: 22)
- `--key <path>` - Override SSH key path
- `--remote-path <path>` - Override remote project directory
- `--restart` - Restart backend after deployment
- `--skip-build` - Skip build, use existing /build directory
- `--dry-run` - Show what would happen without executing
- `--help` - Show help message

---

## Troubleshooting

### "SSH connection failed"

**Problem:** Cannot connect to Lightsail instance

**Solutions:**
1. Check your security group allows SSH (port 22) from your IP
2. Verify SSH key path is correct
3. Ensure key has correct permissions: `chmod 400 key.pem`
4. Test manual connection: `ssh -i key.pem user@host`

### "Frontend build failed"

**Problem:** Build errors during npm run build

**Solutions:**
1. Delete node_modules and reinstall: `rm -rf node_modules && npm install --legacy-peer-deps`
2. Check Node.js version: `node --version` (needs 18+)
3. Run build manually to see errors: `npm run build`

### "rsync not found, will use scp (slower)"

**Problem:** rsync not installed (not critical, just slower)

**Solution:** Install rsync for faster transfers:
```bash
# On local machine (WSL/Linux)
sudo apt install rsync

# On Lightsail instance
ssh to-server
sudo apt install rsync
```

### "Backend restart failed"

**Problem:** Automatic restart didn't work

**Solution:** Restart manually on the server:
```bash
ssh -i ~/.ssh/key.pem ubuntu@your-host
cd /path/to/project
./start_server.sh restart
```

### Build works locally but fails on server

**Problem:** This shouldn't happen anymore! The whole point of this deployment method is building locally.

**Note:** If you ever try to build on the server and it crashes, that's the memory issue we're avoiding. Always build locally and deploy with this script.

---

## Deployment Workflow Examples

### First Time Deployment

```bash
# 1. Setup config
cp .deploy-config.example .deploy-config
nano .deploy-config  # Fill in your details

# 2. Test deployment (dry run)
./deploy-to-lightsail.sh --dry-run

# 3. Deploy for real
./deploy-to-lightsail.sh --restart
```

### Regular Updates After Code Changes

```bash
# Make your frontend changes in src/
# Then deploy:
./deploy-to-lightsail.sh --restart
```

### Quick Re-deploy (Already Built)

```bash
# If you just deployed and need to redeploy the same build:
./deploy-to-lightsail.sh --skip-build --restart
```

---

## What Gets Deployed

The deployment script transfers the entire `/build` directory which contains:

```
build/
├── index.html              # Main SPA entry point
├── _app/                   # SvelteKit app files
│   ├── immutable/         # Hashed, cacheable assets
│   └── version.json       # Build version info
└── static/                # Static assets (images, fonts, etc.)
    ├── favicon.png
    ├── logo.png
    └── ...
```

The backend (`backend/open_webui/main.py`) serves:
- Static files from `build/static/` at `/static`
- SPA files from `build/` at `/` (catch-all for SvelteKit routing)

---

## Understanding the Backend

The backend automatically handles the build directory during startup:

**From `backend/open_webui/env.py:263`:**
```python
FRONTEND_BUILD_DIR = Path(os.getenv("FRONTEND_BUILD_DIR", BASE_DIR / "build"))
```

**From `backend/open_webui/main.py:2327-2336`:**
```python
if os.path.exists(FRONTEND_BUILD_DIR):
    app.mount(
        "/",
        SPAStaticFiles(directory=FRONTEND_BUILD_DIR, html=True),
        name="spa-static-files",
    )
else:
    log.warning(f"Frontend build directory not found at '{FRONTEND_BUILD_DIR}'")
```

So as long as the `/build` directory exists, the backend will serve it automatically. No configuration needed!

---

## Performance Tips

### Use rsync for Faster Transfers

Install rsync on both machines for incremental transfers (only changed files):

```bash
# Local (if not already installed)
sudo apt install rsync

# Remote
ssh to-server
sudo apt install rsync
```

With rsync, subsequent deployments only transfer changed files, making updates much faster.

### Build Caching

The `npm run build` uses Vite's build caching. To clean build cache:

```bash
rm -rf .svelte-kit node_modules/.vite
npm run build
```

---

## Integration with Existing Scripts

This deployment method works alongside your existing scripts:

- **`./start_server.sh`** - Start/stop/restart backend (works same as before)
- **`./start_dev.sh`** - Local development with HMR (for development)
- **`./deploy-to-lightsail.sh`** - Production deployment (build + transfer)

Typical workflow:
1. Develop locally using `./start_dev.sh`
2. Test changes in development mode
3. Deploy to production with `./deploy-to-lightsail.sh --restart`

---

## Security Notes

1. **Never commit `.deploy-config`** - It contains server credentials
   - Already added to `.gitignore`

2. **Protect your SSH keys:**
   ```bash
   chmod 400 ~/.ssh/your-key.pem
   ```

3. **Use SSH key authentication** - Never use password authentication for deployment

4. **Restrict Lightsail security groups** - Only allow SSH from your IP if possible

---

## FAQ

### Do I need to install Node.js on Lightsail?

**No!** That's the beauty of this approach. The server only needs:
- Python 3.11+ (for backend)
- The pre-built frontend files

No Node.js, npm, or build tools needed on the server.

### What if I don't have rsync?

The script automatically falls back to `scp` if rsync isn't available. It's slower but works fine.

### Can I deploy from Windows?

Yes! If you're using WSL2 (which you are), this script works perfectly. If using Windows directly, you'd need to adapt for PowerShell or use WSL.

### Does this work with the official open-webui package?

This setup is for your customized fork. The official `open-webui` pip package includes pre-built frontend assets in the wheel file, so users never build anything - they just `pip install open-webui` and run it.

Your customizations require building, so we build locally (like the official package CI does) and deploy the artifacts.

### How do I check if deployment worked?

After deployment:

1. **Check backend logs:**
   ```bash
   ssh to-server
   cd /path/to/project
   tail -f logs/backend.log
   ```

2. **Run health check:**
   ```bash
   ./health_check.sh
   ```

3. **Access in browser:**
   - Go to your Lightsail public IP or domain
   - You should see your frontend loading

---

## Getting Help

If you encounter issues:

1. Check troubleshooting section above
2. Review deployment logs
3. Test SSH connection manually
4. Verify backend is running: `./start_server.sh status`
5. Check backend logs: `tail -f logs/backend.log`

---

**Last Updated:** 2025-12-27
**Version:** 1.0.0
