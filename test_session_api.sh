#!/bin/bash
# Test the session API to see what it returns

echo "=== Testing Session API ==="
echo "Please provide a valid token for testmanager@test.com"
echo ""
echo "To get a token:"
echo "1. Log in to https://dev.fixxit.ai as testmanager@test.com"
echo "2. Open browser console (F12)"
echo "3. Run: console.log(localStorage.getItem('token'))"
echo "4. Copy the token"
echo ""
read -p "Enter token: " TOKEN

echo ""
echo "Fetching session data from /api/auths/..."
curl -s -H "Authorization: Bearer $TOKEN" https://dev.fixxit.ai/api/auths/ | jq '.'

echo ""
echo "=== Checking managed_groups field ==="
MANAGED_GROUPS=$(curl -s -H "Authorization: Bearer $TOKEN" https://dev.fixxit.ai/api/auths/ | jq -r '.managed_groups')
echo "managed_groups: $MANAGED_GROUPS"

if [ "$MANAGED_GROUPS" = "null" ] || [ "$MANAGED_GROUPS" = "" ]; then
    echo "❌ managed_groups is NULL or empty!"
    echo "This is why the button isn't showing."
else
    echo "✓ managed_groups is set"
fi

echo ""
echo "=== Checking if groups have dashboard URLs ==="
for GROUP_ID in $(echo $MANAGED_GROUPS | jq -r '.[]'); do
    echo "Checking group: $GROUP_ID"
    curl -s -H "Authorization: Bearer $TOKEN" "https://dev.fixxit.ai/api/groups/id/$GROUP_ID" | jq '{id, name, dashboard_url: .data.management_dashboard_url}'
done
