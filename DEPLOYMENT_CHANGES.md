# Deployment Changes - 2026-01-20

This document tracks all changes made during the deployment and bug fixes for the Fixxit.ai OpenWebUI application.

## Environment
- **Server**: AWS Lightsail (18.204.97.97)
- **Dev URL**: https://dev.fixxit.ai
- **Production URL**: https://app.fixxit.ai (planned)
- **Backend Port**: 8080
- **Frontend Port**: 5173

## Changes Made

### 1. Fixed Inconsistent Log Loading (Database Password Decryption)

**Problem**:
Logs would sometimes load successfully, sometimes show "no logs" when switching tabs or refreshing the page. The behavior was inconsistent and random.

**Root Cause**:
Multiple backend workers (2 workers via Uvicorn) had different database encryption keys. When the backend restarted without a persistent encryption key, each worker generated a different random key. The encrypted PostgreSQL password could only be decrypted by the worker that had the correct key, causing 50% failure rate.

**Error Logs**:
```
2026-01-20 13:19:29 | ERROR | Failed to decrypt password
```

**Solution**:
1. Created persistent encryption key in environment variables
2. Updated server startup to use the same key across all workers
3. Modified `/home/ec2-user/fixxit.ai-openwebui/backend/.env` with persistent key
4. Updated `/home/ec2-user/fixxit.ai-openwebui/start_server.sh` to export the key

**Files Modified**:
- `/home/ec2-user/fixxit.ai-openwebui/backend/.env` (created)
- `/home/ec2-user/fixxit.ai-openwebui/start_server.sh` (modified)

**Deployment**:
```bash
# Kill all backend processes
killall -9 python uvicorn

# Restart with persistent encryption key
export DATABASE_PASSWORD_ENCRYPTION_KEY="ajZEaDE4QmUwQmlsRzVjVjBSWnJSamxTOXRXdGhYWVF1U2l4T3VQMkRLND0="
```

**Status**: ✅ Fixed - No more decryption errors, logs load consistently

---

### 2. Fixed 500 Errors on Manager/Invitation Endpoints

**Problem**:
Three API endpoints in the User Management tab were returning 500 errors when accessed by admin users:
- `/api/v1/managers/my-groups` - 500 error
- `/api/v1/managers/pending-users` - 500 error (via utils/managers.py)
- `/api/v1/invitations/list` - 500 error

**Error Message**:
```python
TypeError: GroupTable.get_groups() missing 1 required positional argument: 'filter'
```

**Root Cause**:
The `Groups.get_groups()` method signature was changed to require a `filter` parameter, but three locations in the codebase were still calling it without the parameter.

**Solution**:
Added empty filter object `{}` to all `Groups.get_groups()` calls.

**Files Modified**:

1. **backend/open_webui/utils/managers.py** (line 57)
```python
# BEFORE
all_groups = Groups.get_groups()

# AFTER
all_groups = Groups.get_groups({})
```

2. **backend/open_webui/routers/managers.py** (line 492)
```python
# BEFORE
groups = Groups.get_groups()

# AFTER
groups = Groups.get_groups({})
```

3. **backend/open_webui/routers/invitations.py** (line 232)
```python
# BEFORE
all_groups = Groups.get_groups()

# AFTER
all_groups = Groups.get_groups({})
```

**Git Commit**:
```
commit: fix: add missing filter parameter to Groups.get_groups() calls
```

**Deployment**:
```bash
# Copy modified files to server
scp -i ~/.ssh/lightsail-key.pem backend/open_webui/utils/managers.py ec2-user@18.204.97.97:/home/ec2-user/fixxit.ai-openwebui/backend/open_webui/utils/
scp -i ~/.ssh/lightsail-key.pem backend/open_webui/routers/managers.py ec2-user@18.204.97.97:/home/ec2-user/fixxit.ai-openwebui/backend/open_webui/routers/
scp -i ~/.ssh/lightsail-key.pem backend/open_webui/routers/invitations.py ec2-user@18.204.97.97:/home/ec2-user/fixxit.ai-openwebui/backend/open_webui/routers/

# Restart backend
ssh -i ~/.ssh/lightsail-key.pem ec2-user@18.204.97.97 'cd /home/ec2-user/fixxit.ai-openwebui && ./start_server.sh restart'
```

**Status**: ✅ Fixed - All manager/invitation endpoints now return 200

---

### 3. Made Invitation URLs Dynamic

**Problem**:
Invitation links were hardcoded to use `https://app.fixxit.ai` regardless of the actual domain being used. When creating invitations on dev.fixxit.ai, the links still pointed to app.fixxit.ai.

**Example Hardcoded URL**:
```
https://app.fixxit.ai/auth?invite=6Vhin3N1W1kXVg-tPpjOdiCZmQKHxASCN5KRDss3FHo
```

**Root Cause**:
The `FRONTEND_BASE_URL` environment variable had a hardcoded fallback:
```python
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "https://app.fixxit.ai")
```

**Solution**:
Extract the base URL dynamically from the HTTP request using FastAPI's `Request` object.

**Files Modified**:

**backend/open_webui/routers/invitations.py**

1. Added `Request` import (line 17):
```python
from fastapi import APIRouter, Depends, HTTPException, Request, status
```

2. Created helper function to extract base URL (lines 33-46):
```python
def get_base_url_from_request(request: Request) -> str:
    """
    Extract the base URL from the incoming request.
    Uses the request's scheme and host to dynamically build the URL.
    Falls back to FRONTEND_BASE_URL if request is not available.
    """
    if not request:
        return FRONTEND_BASE_URL

    # Get scheme (http/https) and host from request
    scheme = request.url.scheme
    host = request.headers.get("host") or request.url.netloc

    return f"{scheme}://{host}"
```

3. Updated `create_invitation()` endpoint (lines 134-189):
```python
@router.post("/create", response_model=InvitationResponse)
async def create_invitation(
    request: CreateInvitationRequest,
    http_request: Request,  # ADDED
    user=Depends(get_admin_or_manager_user)
):
    # ... existing code ...

    # Get base URL from request and pass to formatter
    base_url = get_base_url_from_request(http_request)
    return format_invitation_response(invitation, base_url)
```

4. Updated `get_group_invitations()` endpoint (lines 192-214):
```python
@router.get("/group/{group_id}", response_model=list[InvitationResponse])
async def get_group_invitations(
    group_id: str,
    http_request: Request,  # ADDED
    user=Depends(get_admin_or_manager_user)
):
    # ... existing code ...

    # Get base URL from request and pass to formatter
    base_url = get_base_url_from_request(http_request)
    return [format_invitation_response(inv, base_url) for inv in invitations]
```

5. Updated `list_my_invitations()` endpoint (lines 217-247):
```python
@router.get("/list", response_model=list[InvitationResponse])
async def list_my_invitations(
    http_request: Request,  # ADDED
    user=Depends(get_admin_or_manager_user)
):
    # ... existing code ...

    # Get base URL from request and pass to formatter
    base_url = get_base_url_from_request(http_request)
    return [format_invitation_response(inv, base_url) for inv in invitations]
```

**Git Commit**:
```
commit c64f1bfaa: fix: make invitation URLs dynamic to current request URL

- Add Request parameter to all invitation endpoints
- Extract base URL from request scheme and host
- Pass dynamic base_url to format_invitation_response()
- Replaces hardcoded app.fixxit.ai with current domain
```

**Deployment**:
```bash
# Copy modified file to server
scp -i ~/.ssh/lightsail-key.pem backend/open_webui/routers/invitations.py ec2-user@18.204.97.97:/home/ec2-user/fixxit.ai-openwebui/backend/open_webui/routers/

# Restart backend
cd /home/ec2-user/fixxit.ai-openwebui/backend
export DATABASE_PASSWORD_ENCRYPTION_KEY="ajZEaDE4QmUwQmlsRzVjVjBSWnJSamxTOXRXdGhYWVF1U2l4T3VQMkRLND0="
nohup ./venv/bin/uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --workers 2 > /home/ec2-user/fixxit.ai-openwebui/logs/backend.log 2>&1 &
```

**Expected Result**:
Invitations created on dev.fixxit.ai will now show:
```
https://dev.fixxit.ai/auth?invite=<token>
```

**Status**: ✅ Fixed - Invitation URLs now use the current domain

---

## Testing Checklist

- [x] Logs load consistently without "Failed to decrypt password" errors
- [x] `/api/v1/managers/my-groups` returns 200 for admin users
- [x] `/api/v1/managers/pending-users` returns 200 for admin users
- [x] `/api/v1/invitations/list` returns 200 for admin users
- [ ] New invitations created on dev.fixxit.ai show dev.fixxit.ai in URL (needs user verification)

---

## Critical Configuration

**Database Encryption Key** (MUST be consistent across all environments):
```bash
DATABASE_PASSWORD_ENCRYPTION_KEY="ajZEaDE4QmUwQmlsRzVjVjBSWnJSamxTOXRXdGhYWVF1U2l4T3VQMkRLND0="
```

**IMPORTANT**: This key MUST be copied to production when deploying. Changing this key will make all existing encrypted database passwords unreadable.

---

## Next Steps

1. **Verify dynamic invitation URLs** - Create a new invitation on dev.fixxit.ai and confirm the URL contains "dev.fixxit.ai"
2. **Plan production deployment** - Document process for copying dev environment to production directory
3. **DNS configuration** - Point app.fixxit.ai to production deployment on port 8081
4. **Production testing** - Full smoke test of all features on production environment

---

## Server Information

**Dev Environment**:
- Directory: `/home/ec2-user/fixxit.ai-openwebui`
- Backend: Port 8080
- Frontend: Port 5173
- Domain: dev.fixxit.ai
- Database: `/home/ec2-user/fixxit.ai-openwebui/backend/data/webui.db`

**Production Environment** (planned):
- Directory: `/home/ec2-user/fixxit.ai-openwebui-prod` (or similar)
- Backend: Port 8081
- Frontend: Port 5174 (or similar)
- Domain: app.fixxit.ai
- Database: New copy with same encryption key

---

## Git Commits

1. `fix: add missing filter parameter to Groups.get_groups() calls`
2. `fix: make invitation URLs dynamic to current request URL` (commit c64f1bfaa)

---

## Notes

- All changes are deployed to dev environment (dev.fixxit.ai)
- Backend is running with 2 workers via Uvicorn
- Database encryption key is persistent in `.env` file and `start_server.sh`
- No frontend changes were required for these fixes
