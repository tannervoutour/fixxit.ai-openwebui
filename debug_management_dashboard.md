# Debug Management Dashboard Button Not Showing

## Quick Diagnosis Steps

### Step 1: Check Browser Console (Do this first!)

The ManagementDashboardButton has extensive logging built in.

1. Open the app in your browser
2. Open Developer Tools (F12)
3. Go to Console tab
4. Look for messages starting with `[Management Dashboard]`

**Expected logs:**
```
[Management Dashboard] User role: manager
[Management Dashboard] User managed_groups: ["group-id-1", "group-id-2"]
[Management Dashboard] Loading managed groups...
[Management Dashboard] Fetching group: group-id-1
[Management Dashboard] Full group data: {...}
[Management Dashboard] Dashboard URL: https://example.com
[Management Dashboard] Added group with dashboard: Group Name
[Management Dashboard] Final available groups: [...]
```

**What to look for:**
- If you see "Not a manager, skipping" → User role is not set to 'manager'
- If you see "No managed groups assigned" → User doesn't have managed_groups set
- If groups are fetched but "Dashboard URL: undefined" → Groups don't have dashboard URL configured

### Step 2: Check User Data in Browser

In browser console, run:
```javascript
// Check current user data
JSON.parse(localStorage.getItem('user'))

// Should show:
// {
//   role: "manager",
//   managed_groups: ["group-id-1", "group-id-2"],
//   ...
// }
```

### Step 3: Check Session API Response

In browser console or Network tab:
```javascript
// Check session endpoint
fetch('/api/auths/', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('token')
  }
}).then(r => r.json()).then(console.log)

// Look for:
// {
//   role: "manager",
//   managed_groups: ["..."],
//   ...
// }
```

### Step 4: Check Group Configuration

In Admin panel → Groups → Edit Group → Management Dashboard tab:
- Is the "Management Dashboard URL" field filled in?
- Does it have a valid URL like `https://cooperativekny.fixxit.ai`?

## Common Issues and Fixes

### Issue 1: User is not marked as Manager

**Symptom:** Console shows "Not a manager, skipping"

**Fix:** Update user role in database

```sql
-- Check user role
SELECT id, email, role, managed_groups FROM user WHERE email = 'manager@example.com';

-- Update role to manager
UPDATE user SET role = 'manager' WHERE email = 'manager@example.com';
```

### Issue 2: User has no managed_groups assigned

**Symptom:** Console shows "No managed groups assigned to this manager"

**Fix:** Assign groups to manager

```sql
-- Check current managed_groups
SELECT id, email, role, managed_groups FROM user WHERE email = 'manager@example.com';

-- Update managed_groups (JSON array of group IDs)
UPDATE user
SET managed_groups = '["group-id-1", "group-id-2"]'
WHERE email = 'manager@example.com';

-- Or via UI: Admin panel → Users → Edit User → Managed Groups
```

**IMPORTANT:** The `managed_groups` field must be:
- A JSON array of strings: `["group-id-1", "group-id-2"]`
- NOT NULL or empty array `[]`

### Issue 3: Group doesn't have Dashboard URL configured

**Symptom:** Console shows "Dashboard URL: undefined" or "Final available groups: []"

**Fix:** Configure dashboard URL for group

Via UI:
1. Go to Admin panel → Groups
2. Click Edit on the group
3. Go to "Management Dashboard" tab
4. Enter the dashboard URL (e.g., `https://cooperativekny.fixxit.ai`)
5. Click Save

Via Database:
```sql
-- Check group data
SELECT id, name, data FROM "group" WHERE id = 'group-id-1';

-- Update group data to include management_dashboard_url
UPDATE "group"
SET data = json_set(COALESCE(data, '{}'), '$.management_dashboard_url', 'https://cooperativekny.fixxit.ai')
WHERE id = 'group-id-1';
```

### Issue 4: Frontend Cache Issue

**Symptom:** Everything looks correct in database but button still doesn't show

**Fix:** Clear browser cache and reload

1. Open Developer Tools (F12)
2. Right-click the reload button
3. Select "Empty Cache and Hard Reload"
4. Or: Clear localStorage and re-login
   ```javascript
   localStorage.clear();
   location.reload();
   ```

## Manual Debugging Script

Run this in browser console to debug:

```javascript
// Get current user
const user = JSON.parse(localStorage.getItem('user'));
console.log('User Role:', user.role);
console.log('Managed Groups:', user.managed_groups);

// Fetch session to verify
fetch('/api/auths/', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('token')
  }
}).then(r => r.json()).then(session => {
  console.log('Session Role:', session.role);
  console.log('Session Managed Groups:', session.managed_groups);

  // Fetch each managed group
  if (session.managed_groups && session.managed_groups.length > 0) {
    session.managed_groups.forEach(groupId => {
      fetch(`/api/groups/id/${groupId}`, {
        headers: {
          'Authorization': 'Bearer ' + localStorage.getItem('token')
        }
      }).then(r => r.json()).then(group => {
        console.log(`Group ${group.name}:`, {
          id: group.id,
          dashboard_url: group.data?.management_dashboard_url
        });
      });
    });
  }
});
```

## Expected Correct Setup

For the button to show, you need:

1. **User record:**
   ```json
   {
     "role": "manager",
     "managed_groups": ["abc123", "def456"]
   }
   ```

2. **Group record (at least one):**
   ```json
   {
     "id": "abc123",
     "name": "My Group",
     "data": {
       "management_dashboard_url": "https://cooperativekny.fixxit.ai"
     }
   }
   ```

3. **Session response includes managed_groups:**
   ```json
   {
     "role": "manager",
     "managed_groups": ["abc123", "def456"]
   }
   ```

## Need to Set Dashboard URL via API?

If UI doesn't work, use API directly:

```bash
# Get group details
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://dev.fixxit.ai/api/groups/id/GROUP_ID

# Update group with dashboard URL
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Group Name",
    "description": "Group Description",
    "data": {
      "management_dashboard_url": "https://cooperativekny.fixxit.ai"
    }
  }' \
  https://dev.fixxit.ai/api/groups/id/GROUP_ID/update
```
