# Fixxit.ai OpenWebUI Internal Setup Documentation

## Overview

This document provides a complete record of how the Fixxit.ai OpenWebUI development environment was set up, including all steps taken, issues encountered, and solutions implemented.

## Repository Information

- **Repository**: https://github.com/tannervoutour/fixxit.ai-openwebui.git
- **Upstream**: https://github.com/open-webui/open-webui.git
- **Main Development Branch**: `fixxit-main`
- **Technology Stack**: Svelte (Frontend) + Python FastAPI (Backend)

## Setup History & Process

### 1. Initial Repository Setup (Completed)

**What We Did:**
- Forked the official OpenWebUI repository to `tannervoutour/fixxit.ai-openwebui`
- Created `fixxit-main` branch for all Fixxit.ai customizations
- Set up automated upstream sync workflow
- Configured SSH keys for repository access

**Key Files Created:**
- `.github/workflows/sync-upstream.yml` - Automated sync with upstream OpenWebUI
- `FIXXIT_SETUP.md` - Basic setup guide
- `docker-compose.fixxit.yml` - Production Docker configuration
- `.env.fixxit.example` - Environment template with Fixxit.ai branding

### 2. Development Environment Setup (Completed)

**Node.js Upgrade Process:**
- **Issue**: OpenWebUI requires Node.js 20+, system had 18.20.8
- **Solution**: Installed Node Version Manager (nvm) and upgraded to Node.js 22.21.1

```bash
# Commands used:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install 22
nvm use 22
nvm alias default 22
```

**Dependency Installation:**
- **Backend**: Used existing Python virtual environment with all dependencies
- **Frontend**: Required `--legacy-peer-deps` flag due to dependency conflicts

```bash
# Frontend dependencies:
npm install --legacy-peer-deps
npm install y-protocols --legacy-peer-deps  # Additional dependency fix
```

### 3. Development Servers Setup (Completed)

**Backend Server (Python FastAPI):**
- **Port**: 8080
- **Command**: `python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --reload`
- **Database**: SQLite (auto-created at `backend/data/webui.db`)
- **Status**: ✅ Fully functional with hot reload

**Frontend Server (Svelte):**
- **Port**: 5173
- **Command**: `npm run dev`
- **Purpose**: Hot reload development, compiles Svelte components
- **Status**: ✅ Running with hot reload capability

## Current Working Environment

### Access Points
- **Full Application**: http://localhost:8080
- **Frontend Dev Server**: http://localhost:5173 (for development only)
- **API Documentation**: http://localhost:8080/docs

### Development Workflow
1. **Make changes** to files in `src/` directory
2. **Frontend server (5173)** automatically compiles changes
3. **Refresh** http://localhost:8080 to see changes in full application

### Key Directories for Customization
- `src/lib/components/` - UI components
- `src/routes/` - Page layouts and routing
- `src/app.html` - Main HTML template
- `static/` - Static assets (logos, images, etc.)
- `tailwind.config.js` - Styling configuration

## Issues Encountered & Solutions

### Issue 1: Node.js Version Incompatibility
- **Problem**: OpenWebUI requires Node.js 20+, system had 18.20.8
- **Solution**: Installed nvm and upgraded to Node.js 22.21.1
- **Status**: ✅ Resolved

### Issue 2: NPM Dependency Conflicts
- **Problem**: `@tiptap/extension-bubble-menu` version conflicts
- **Solution**: Used `--legacy-peer-deps` flag for npm install
- **Status**: ✅ Resolved

### Issue 3: Missing y-protocols Dependency
- **Problem**: Frontend build failed due to missing `y-protocols/awareness`
- **Solution**: Manually installed `y-protocols` package
- **Status**: ✅ Resolved

### Issue 4: Docker Development Setup Complexity
- **Problem**: Docker build taking too long, complex dependency management
- **Solution**: Used local development setup instead of Docker for development
- **Status**: ✅ Resolved (Docker configs kept for future production use)

## File Structure Overview

```
fixxit.ai-openwebui/
├── .github/workflows/
│   └── sync-upstream.yml           # Automated upstream sync
├── backend/                        # Python FastAPI backend
│   ├── data/                      # SQLite database location
│   ├── open_webui/               # Main backend code
│   └── requirements.txt          # Python dependencies
├── src/                           # Svelte frontend source
│   ├── lib/components/           # UI components
│   ├── routes/                   # Page routing
│   └── app.html                  # Main HTML template
├── static/                       # Static assets
├── custom/                       # Custom Fixxit.ai assets
├── docker-compose.fixxit.yml     # Production Docker config
├── docker-compose.dev.yml        # Development Docker config (optional)
├── .env.fixxit.example           # Environment template
├── FIXXIT_SETUP.md              # Basic setup guide
└── package.json                  # Node.js dependencies
```

## Environment Configuration

### Required Environment Variables
```bash
WEBUI_NAME="Fixxit.ai"
WEBUI_URL="http://localhost:8080"
DEFAULT_THEME="dark"
SHOW_ADMIN_DETAILS="false"
```

### Database Configuration
- **Type**: SQLite (development)
- **Location**: `backend/data/webui.db`
- **Auto-created**: Yes, on first run

## Automation & Sync

### Upstream Sync Workflow
- **Trigger**: Runs every Monday and Thursday at 7:00 AM UTC, or manual trigger
- **Function**: Syncs latest changes from upstream OpenWebUI repository
- **Conflict Handling**: Creates PRs for clean merges, issues for conflicts
- **Branch Management**: Updates `upstream-main` branch automatically

### Development vs Production
- **Development**: Local servers with hot reload
- **Production**: Docker deployment using `docker-compose.fixxit.yml`

## Next Steps for Customization

1. **UI Branding**: Modify logos, colors, and text in `src/` directory
2. **Custom Components**: Create Fixxit.ai-specific components
3. **Styling**: Update `tailwind.config.js` and component styles
4. **Assets**: Replace logos and images in `static/` directory

## Support & Maintenance

### Regular Maintenance Tasks
- Monitor automated sync PRs/issues
- Review upstream changes for compatibility
- Test customizations after upstream updates
- Update documentation as changes are made

### Key Commands for Development
```bash
# Start backend server
source venv/bin/activate
cd backend
python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --reload

# Start frontend server (in separate terminal)
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
nvm use 22
npm run dev
```

## Contact & Repository Access
- **Repository Owner**: tannervoutour
- **SSH Access**: Configured for read/write access
- **Branch Protection**: Main development occurs on `fixxit-main` branch

---

**Document Last Updated**: December 6, 2025  
**Environment Status**: ✅ Fully Functional Development Environment  
**Ready for Customization**: ✅ Yes