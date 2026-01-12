# Archived Files

This directory contains files that are not currently used in the Fixxit.ai deployment.

## Archive Date
December 27, 2025

## Reason for Archiving

### Docker Files
**Why archived:** Not using Docker deployment. Using direct Python/Node.js deployment on Lightsail instead.

**Files:**
- All Dockerfile variants
- All docker-compose.yaml files  
- .dockerignore
- Docker-related scripts (run.sh, run-compose.sh, run-ollama-docker.sh)

### Kubernetes Files
**Why archived:** Not using Kubernetes. Deploying to single Lightsail instance.

### Obsolete Scripts
**Why archived:** Replaced by newer, more comprehensive scripts.

**Replaced by:**
- `backend/start.sh` → Replaced by `start_server.sh` (main directory)
- `backend/dev.sh` → Replaced by `start_dev.sh` (main directory)
- `confirm_remove.sh` → Docker-specific cleanup (not needed)
- `update_ollama_models.sh` → Docker-specific (not needed)

### Upstream Development Tools
**Why archived:** Tools for OpenWebUI core development, not needed for customization.

**Files:**
- contribution_stats.py
- Makefile

## Current Deployment Method

We use a **local build + remote deploy** strategy:
1. Build frontend locally (avoids memory issues)
2. Commit source code to GitHub
3. Deploy built files to Lightsail via rsync
4. Backend runs directly with Python venv (no Docker)

See `WORKFLOW.md` for complete deployment documentation.

## Restoring Files

If you need any of these files:
```bash
# Example: Restore a Docker file
cp archive/docker/Dockerfile .
```

## Contents

```
archive/
├── docker/           # All Docker-related files
├── kubernetes/       # Kubernetes deployment files
├── scripts/          # Obsolete/superseded scripts  
└── docs/             # Archived documentation
```
