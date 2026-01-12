"""
Manager role utilities and permission checks.

The manager role allows users to:
- Manage users within their assigned groups
- Approve pending users for their groups
- Create and manage invitations for their groups
- Full user CRUD operations (delete, edit, etc.) for their group members
"""

from typing import Optional
from open_webui.models.users import UserModel
from open_webui.models.groups import Groups, GroupMembers


def is_manager(user: UserModel) -> bool:
    """Check if user has manager role"""
    return user.role == "manager"


def is_admin(user: UserModel) -> bool:
    """Check if user has admin role"""
    return user.role == "admin"


def is_admin_or_manager(user: UserModel) -> bool:
    """Check if user has admin or manager role"""
    return user.role in ["admin", "manager"]


def can_manage_group(user: UserModel, group_id: str) -> bool:
    """
    Check if user can manage the specified group.

    Admins can manage all groups.
    Managers can only manage groups in their managed_groups list.
    """
    if is_admin(user):
        return True

    if is_manager(user):
        if user.managed_groups and group_id in user.managed_groups:
            return True

    return False


def get_managed_groups(user: UserModel) -> list[str]:
    """
    Get list of group IDs that user can manage.

    Admins can manage all groups (returns empty list to indicate "all").
    Managers get their managed_groups list.
    """
    if is_admin(user):
        # Return all group IDs
        all_groups = Groups.get_groups()
        return [group.id for group in all_groups]

    if is_manager(user) and user.managed_groups:
        return user.managed_groups

    return []


def can_manage_user(manager: UserModel, target_user_id: str) -> bool:
    """
    Check if manager can manage a specific user.

    Manager can manage user if:
    - They are an admin (can manage all users)
    - They are a manager and user belongs to one of their managed groups
    """
    if is_admin(manager):
        return True

    if is_manager(manager) and manager.managed_groups:
        # Check if target user is in any of manager's groups
        for group_id in manager.managed_groups:
            if GroupMembers.is_user_in_group(target_user_id, group_id):
                return True

    return False


def get_manageable_users(manager: UserModel) -> list[str]:
    """
    Get list of user IDs that this manager can manage.

    Returns user IDs from all groups the manager is assigned to.
    """
    user_ids = set()

    if is_admin(manager):
        # Admins can manage all users - return indicator
        return ["*"]  # Special marker for "all users"

    if is_manager(manager) and manager.managed_groups:
        for group_id in manager.managed_groups:
            members = GroupMembers.get_group_members(group_id)
            user_ids.update([member.user_id for member in members])

    return list(user_ids)


def add_managed_group(user: UserModel, group_id: str) -> UserModel:
    """Add a group to user's managed_groups list"""
    from open_webui.models.users import Users

    if not user.managed_groups:
        user.managed_groups = []

    if group_id not in user.managed_groups:
        user.managed_groups.append(group_id)
        Users.update_user_by_id(
            user.id,
            {"managed_groups": user.managed_groups}
        )

    return user


def remove_managed_group(user: UserModel, group_id: str) -> UserModel:
    """Remove a group from user's managed_groups list"""
    from open_webui.models.users import Users

    if user.managed_groups and group_id in user.managed_groups:
        user.managed_groups.remove(group_id)
        Users.update_user_by_id(
            user.id,
            {"managed_groups": user.managed_groups}
        )

    return user


def get_pending_users_for_manager(manager: UserModel) -> list:
    """
    Get pending users that this manager can approve.

    Returns users where:
    - role = "pending"
    - pending_group_id is in manager's managed_groups
    """
    from open_webui.models.users import Users

    if is_admin(manager):
        # Admins see all pending users
        return Users.get_users(skip=0, limit=1000)  # TODO: Add filtering by role

    if is_manager(manager) and manager.managed_groups:
        # Get pending users for manager's groups
        all_users = Users.get_users(skip=0, limit=1000)
        pending_users = [
            user for user in all_users
            if user.role == "pending"
            and user.pending_group_id in manager.managed_groups
        ]
        return pending_users

    return []
