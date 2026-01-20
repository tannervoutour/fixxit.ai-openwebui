# Management Dashboard button not appearing on initial login for managers

## Description
The Management Dashboard button does not appear for manager users immediately after login. The button only becomes visible after reloading the page.

## Impact
- **Severity:** Low (workaround exists)
- **Users affected:** Managers only
- **Workaround:** Reload the page after login

## Expected Behavior
The Management Dashboard button should appear immediately after a manager logs in, without requiring a page reload.

## Actual Behavior
- On initial login: Button does not appear
- After page reload: Button appears correctly
- All subsequent navigation: Button works as expected

## Environment
- **Browser:** Tested in both normal and incognito mode (rules out cache issue)
- **Component:** `src/lib/components/chat/ManagementDashboardButton.svelte`
- **Backend:** Session API correctly returns `managed_groups` field

## Investigation Summary
1. ✅ Database configuration verified - correct
2. ✅ Backend API verified - `/api/auths/` correctly returns `managed_groups`
3. ✅ Not a cache issue - persists in incognito mode
4. ❌ Svelte reactivity not triggering on initial user store population

## Technical Details
**Component Location:** `src/lib/components/chat/ManagementDashboardButton.svelte:132`

**Display Condition:**
```svelte
{#if $user?.role === 'manager' && availableGroups.length > 0 && !loading}
```

**Suspected Root Cause:**
The component mounts during the login navigation flow, but the `$user` store is populated slightly after mount via `user.set(sessionUser)` in `src/routes/auth/+page.svelte:51`. The reactive statement watching `$user.managed_groups` may not be triggering when the user object is initially set.

## Attempted Fixes
1. Changed reactive statement to watch `JSON.stringify($user.managed_groups)` - no effect
2. Added direct `$user` watching with extensive logging - no effect
3. Added `previousManagedGroupsJson` tracking + `setTimeout()` - no effect
4. Console logs show component reactive statements are not firing at all on initial login

## Potential Solutions
1. Use explicit store subscription instead of reactive statements
2. Trigger component re-render from auth page after user is set
3. Investigate SvelteKit layout/page lifecycle timing
4. Consider moving button to a location that mounts after auth is complete

## Related Files
- `src/lib/components/chat/ManagementDashboardButton.svelte`
- `src/routes/auth/+page.svelte`
- `src/lib/components/chat/Navbar.svelte`
- `backend/open_webui/routers/auths.py`
