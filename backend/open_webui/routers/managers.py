"""
Manager-specific user management router.

Managers can perform full user management operations on users within their groups:
- View pending users for their groups
- Approve/reject pending users
- Delete users
- Edit user details (name, email, password)
- Add existing users to their groups
- Remove users from their groups
- View all group members
"""

import logging
import time
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, EmailStr

from open_webui.models.users import Users, UserModel
from open_webui.models.groups import Groups, GroupMembers
from open_webui.models.auths import Auths
from open_webui.utils.auth import get_admin_or_manager_user, get_password_hash
from open_webui.utils.managers import (
    can_manage_group,
    can_manage_user,
    get_managed_groups,
    get_pending_users_for_manager,
    is_admin
)
from open_webui.utils.access_control import get_permissions
from open_webui.constants import ERROR_MESSAGES

logger = logging.getLogger(__name__)
router = APIRouter()


############################
# Request/Response Models
############################


class PendingUserResponse(BaseModel):
    """Response model for pending user with group info"""
    id: str
    name: str
    email: str
    role: str
    pending_group_id: Optional[str]
    pending_group_name: Optional[str]
    profile_image_url: str
    created_at: int


class ApproveUserRequest(BaseModel):
    """Request to approve a pending user"""
    user_id: str = Field(..., description="User ID to approve")


class EditUserRequest(BaseModel):
    """Request to edit user details"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class AddUserToGroupRequest(BaseModel):
    """Request to add user to group"""
    user_id: str = Field(..., description="User ID to add")


class GroupMemberResponse(BaseModel):
    """Response model for group member"""
    id: str
    name: str
    email: str
    role: str
    profile_image_url: str
    last_active_at: int
    created_at: int


############################
# Helper Functions
############################


def format_pending_user(user: UserModel) -> PendingUserResponse:
    """Format pending user with group details"""
    group_name = None
    if user.pending_group_id:
        group = Groups.get_group_by_id(user.pending_group_id)
        group_name = group.name if group else None

    return PendingUserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        pending_group_id=user.pending_group_id,
        pending_group_name=group_name,
        profile_image_url=user.profile_image_url,
        created_at=user.created_at
    )


def format_group_member(user: UserModel) -> GroupMemberResponse:
    """Format group member response"""
    return GroupMemberResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        profile_image_url=user.profile_image_url,
        last_active_at=user.last_active_at,
        created_at=user.created_at
    )


############################
# API Endpoints
############################


@router.get("/pending-users", response_model=List[PendingUserResponse])
async def get_pending_users(
    user=Depends(get_admin_or_manager_user)
):
    """
    Get pending users for manager's groups.

    Managers see only users with pending_group_id in their managed groups.
    Admins see all pending users.
    """
    if is_admin(user):
        # Admin sees all pending users
        all_users = Users.get_users()
        pending_users = [u for u in all_users if u.role == "pending"]
    else:
        # Manager sees only their group's pending users
        pending_users = get_pending_users_for_manager(user)

    return [format_pending_user(u) for u in pending_users]


@router.post("/approve-user")
async def approve_user(
    request: ApproveUserRequest,
    manager=Depends(get_admin_or_manager_user)
):
    """
    Approve a pending user and add them to their pending group.

    Manager can only approve users assigned to their groups.
    """
    # Get the pending user
    pending_user = Users.get_user_by_id(request.user_id)

    if not pending_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if pending_user.role != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not pending approval"
        )

    # Check if manager has permission to approve this user
    if not is_admin(manager):
        if not pending_user.pending_group_id or \
           not can_manage_group(manager, pending_user.pending_group_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to approve this user"
            )

    # Update user role to 'user'
    Users.update_user_by_id(request.user_id, {"role": "user"})

    # Add user to their pending group if specified
    if pending_user.pending_group_id:
        GroupMembers.add_user_to_group(request.user_id, pending_user.pending_group_id)
        # Clear pending_group_id after adding to group
        Users.update_user_by_id(request.user_id, {"pending_group_id": None})

    logger.info(f"User {request.user_id} approved by manager {manager.id}")

    return {
        "success": True,
        "message": "User approved successfully",
        "user_id": request.user_id
    }


@router.post("/reject-user/{user_id}")
async def reject_user(
    user_id: str,
    manager=Depends(get_admin_or_manager_user)
):
    """
    Reject and delete a pending user.

    Manager can only reject users assigned to their groups.
    """
    # Get the pending user
    pending_user = Users.get_user_by_id(user_id)

    if not pending_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if pending_user.role != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not pending approval"
        )

    # Check permissions
    if not is_admin(manager):
        if not pending_user.pending_group_id or \
           not can_manage_group(manager, pending_user.pending_group_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to reject this user"
            )

    # Delete the user
    Users.delete_user_by_id(user_id)
    Auths.delete_auth_by_id(user_id)

    logger.info(f"User {user_id} rejected and deleted by manager {manager.id}")

    return {
        "success": True,
        "message": "User rejected and removed successfully"
    }


@router.get("/groups/{group_id}/members", response_model=List[GroupMemberResponse])
async def get_group_members(
    group_id: str,
    manager=Depends(get_admin_or_manager_user)
):
    """
    Get all members of a specific group.

    Manager can only view members of groups they manage.
    """
    # Check permissions
    if not can_manage_group(manager, group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this group's members"
        )

    # Get group members
    members = GroupMembers.get_group_members(group_id)
    member_users = [Users.get_user_by_id(m.user_id) for m in members]
    member_users = [u for u in member_users if u]  # Filter out None

    return [format_group_member(u) for u in member_users]


@router.post("/groups/{group_id}/add-user")
async def add_user_to_group(
    group_id: str,
    request: AddUserToGroupRequest,
    manager=Depends(get_admin_or_manager_user)
):
    """
    Add an existing user to a group.

    Manager can only add users to groups they manage.
    """
    # Check permissions
    if not can_manage_group(manager, group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add users to this group"
        )

    # Verify user exists
    user = Users.get_user_by_id(request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user is already in group
    if GroupMembers.is_user_in_group(request.user_id, group_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already in this group"
        )

    # Add user to group
    GroupMembers.add_user_to_group(request.user_id, group_id)

    logger.info(f"User {request.user_id} added to group {group_id} by manager {manager.id}")

    return {
        "success": True,
        "message": "User added to group successfully"
    }


@router.delete("/groups/{group_id}/remove-user/{user_id}")
async def remove_user_from_group(
    group_id: str,
    user_id: str,
    manager=Depends(get_admin_or_manager_user)
):
    """
    Remove a user from a group.

    Manager can only remove users from groups they manage.
    """
    # Check permissions
    if not can_manage_group(manager, group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to remove users from this group"
        )

    # Get the target user
    target_user = Users.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent managers from removing admin users
    if target_user.role == "admin" and not is_admin(manager):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers cannot remove admin users from groups"
        )

    # Verify user is in group
    if not GroupMembers.is_user_in_group(user_id, group_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not in this group"
        )

    # Remove user from group
    GroupMembers.remove_user_from_group(user_id, group_id)

    logger.info(f"User {user_id} removed from group {group_id} by manager {manager.id}")

    return {
        "success": True,
        "message": "User removed from group successfully"
    }


@router.put("/users/{user_id}")
async def edit_user(
    user_id: str,
    request: EditUserRequest,
    manager=Depends(get_admin_or_manager_user)
):
    """
    Edit user details (name, email, password).

    Manager can only edit users in groups they manage.
    """
    # Get the user
    target_user = Users.get_user_by_id(user_id)

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent managers from editing admin users
    if target_user.role == "admin" and not is_admin(manager):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers cannot edit admin users"
        )

    # Check permissions
    if not is_admin(manager) and not can_manage_user(manager, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this user"
        )

    # Build update dict
    updates = {}
    if request.name:
        updates["name"] = request.name
    if request.email:
        # Check if email is already taken
        existing = Users.get_user_by_email(request.email.lower())
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.EMAIL_TAKEN
            )
        updates["email"] = request.email.lower()

    # Update user
    if updates:
        Users.update_user_by_id(user_id, updates)

    # Update password separately if provided
    if request.password:
        hashed = get_password_hash(request.password)
        Auths.update_user_password_by_id(user_id, hashed)

    logger.info(f"User {user_id} edited by manager {manager.id}")

    return {
        "success": True,
        "message": "User updated successfully"
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    manager=Depends(get_admin_or_manager_user)
):
    """
    Delete a user permanently.

    Manager can only delete users in groups they manage.
    """
    # Get the user
    target_user = Users.get_user_by_id(user_id)

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent deletion of admin users by managers
    if target_user.role == "admin" and not is_admin(manager):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers cannot delete admin users"
        )

    # Check permissions
    if not is_admin(manager) and not can_manage_user(manager, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this user"
        )

    # Delete user
    Users.delete_user_by_id(user_id)
    Auths.delete_auth_by_id(user_id)

    logger.info(f"User {user_id} deleted by manager {manager.id}")

    return {
        "success": True,
        "message": "User deleted successfully"
    }


@router.get("/my-groups")
async def get_my_managed_groups(
    manager=Depends(get_admin_or_manager_user)
):
    """
    Get list of groups this manager can manage.

    Admins get all groups, managers get their assigned groups.
    """
    logger.info(f"get_my_managed_groups called by user {manager.id}, role: {manager.role}")
    logger.info(f"Manager managed_groups field: {manager.managed_groups}, type: {type(manager.managed_groups)}")

    managed_group_ids = get_managed_groups(manager)
    logger.info(f"Managed group IDs: {managed_group_ids}")

    if is_admin(manager):
        # Admin gets all groups
        groups = Groups.get_groups()
    else:
        # Manager gets only their assigned groups
        groups = [Groups.get_group_by_id(gid) for gid in managed_group_ids]
        groups = [g for g in groups if g]  # Filter out None

    return {
        "groups": [
            {
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "member_count": Groups.get_group_member_count_by_id(g.id)
            }
            for g in groups
        ]
    }
