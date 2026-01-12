# Fixxit.ai OpenWebUI Setup Guide

## Repository Structure

- `main` - Original OpenWebUI main branch (synced from upstream)
- `upstream-main` - Latest upstream changes (auto-updated by GitHub Actions)
- `fixxit-main` - Your customization branch (main development branch)
- `feature/*` - Feature branches (branch from fixxit-main)

## Initial Setup Complete ✅

This repository has been automatically configured with:
- ✅ Automated upstream sync workflow
- ✅ Custom environment configuration
- ✅ Docker deployment setup
- ✅ Branch structure for development
- ✅ Development environment fully configured
- ✅ Node.js 22.21.1 installed via nvm
- ✅ All dependencies installed and working

## Current Working Environment (Ready to Use)

### Quick Status Check
- **Backend**: http://localhost:8080 (Full OpenWebUI application)
- **Frontend Dev**: http://localhost:5173 (Hot reload development)
- **Node.js**: v22.21.1 (managed by nvm)
- **Python**: Virtual environment with all backend dependencies

### Start Development Servers (if not running)
```bash
# Backend Server
source venv/bin/activate && cd backend
python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --reload

# Frontend Development Server (separate terminal)
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh" && nvm use 22
npm run dev
```

## Development Environment Setup

### 1. Install Dependencies
```bash
# Install Node.js dependencies (frontend)
npm install

# Install Python dependencies (backend)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment file and configure
cp .env.fixxit.example .env
# Edit .env with your actual API keys and settings
```

### 2. Run Development Environment
```bash
# Terminal 1 - Frontend (Svelte)
npm run dev
# Access at http://localhost:5173

# Terminal 2 - Backend (Python)
source venv/bin/activate
sh dev.sh
# API docs at http://localhost:8080/docs
```

## Development Workflow

### Making Changes
```bash
# Always branch from fixxit-main for new features
git checkout fixxit-main
git pull origin fixxit-main
git checkout -b feature/your-feature-name

# Make your changes...
git add .
git commit -m "feat: your feature description"
git push -u origin feature/your-feature-name

# Create PR to merge into fixxit-main
```

### Syncing with Upstream
The GitHub Action automatically:
1. Runs every Monday and Thursday at 7:00 AM UTC
2. Syncs upstream changes to `upstream-main` branch
3. Creates PR if no conflicts detected
4. Creates issue if conflicts need manual resolution

### Manual Sync (if needed)
```bash
git checkout fixxit-main
git fetch upstream
git merge upstream/main

# If conflicts, resolve them in your IDE
git add .
git commit -m "resolve: upstream merge conflicts"
git push origin fixxit-main
```

## Customization Areas

### Frontend (Svelte)
- `src/lib/components/` - UI components
- `src/routes/` - Page routes
- `src/app.html` - Main HTML template
- `tailwind.config.js` - Styling configuration

### Backend (Python)
- `backend/` - Python API backend
- `backend/apps/` - Application modules
- `backend/config.py` - Configuration

### Styling & Branding
- `src/lib/assets/` - Images, logos
- `static/` - Static assets
- Custom CSS in component files

## Docker Deployment

### Development
```bash
# Build and run with custom configuration
docker-compose -f docker-compose.fixxit.yml up -d

# View logs
docker-compose -f docker-compose.fixxit.yml logs -f
```

### Production
```bash
# Build your customized image
docker build -t fixxit/openwebui:latest .

# Deploy with production settings
docker run -d \
  -p 3000:8080 \
  -v fixxit-openwebui:/app/backend/data \
  --name fixxit-openwebui \
  --restart always \
  fixxit/openwebui:latest
```

## Important Notes

1. **Never commit directly to `main` or `upstream-main`**
2. **All development happens on `fixxit-main` and feature branches**
3. **Test changes locally before pushing**
4. **Review upstream sync PRs carefully**
5. **Keep your customizations modular for easier merging**

## Next Steps

1. **Configure Environment**: Copy `.env.fixxit.example` to `.env` and add your API keys
2. **Start Development**: Run `npm install` and `pip install -r requirements.txt`
3. **Test Setup**: Start both frontend and backend servers
4. **Begin Customization**: Create feature branches from `fixxit-main`

## Troubleshooting

### Common Issues
- **Port conflicts**: Change ports in dev.sh or npm run dev
- **Python dependencies**: Ensure virtual environment is activated
- **Node memory**: Increase Node.js memory limit if needed
- **Database issues**: Check data volume mounts in Docker

### Getting Help
- Check OpenWebUI docs: https://docs.openwebui.com
- Review GitHub issues in upstream repo
- Test changes in development environment first

## Repository Info
- **Repository**: git@github.com:tannervoutour/fixxit.ai-openwebui.git
- **Main Branch**: fixxit-main
- **Upstream**: https://github.com/open-webui/open-webui.git