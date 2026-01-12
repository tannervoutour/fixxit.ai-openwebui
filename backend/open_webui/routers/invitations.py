"""
Invitations router for manager-generated invitation links.

Managers and admins can:
- Create invitation links for their groups
- List invitations for their groups
- Revoke/disable invitations
- View invitation usage statistics
"""

import logging
import secrets
import time
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from open_webui.models.invitations import Invitations, InvitationModel
from open_webui.models.groups import Groups
from open_webui.utils.auth import get_admin_or_manager_user, get_current_user
from open_webui.utils.managers import can_manage_group, get_managed_groups
from open_webui.constants import ERROR_MESSAGES

logger = logging.getLogger(__name__)
router = APIRouter()

# Get frontend URL from environment variable, default to production
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "https://app.fixxit.ai")


############################
# Request/Response Models
############################


class CreateInvitationRequest(BaseModel):
    """Request model for creating new invitation"""
    group_id: str = Field(..., description="Group ID for invitation")
    max_uses: Optional[int] = Field(None, description="Maximum uses (null = unlimited)")
    expires_in_hours: Optional[int] = Field(None, description="Hours until expiration (null = never)")
    note: Optional[str] = Field(None, description="Optional note about invitation purpose")


class InvitationResponse(BaseModel):
    """Response model for invitation with link"""
    id: str
    group_id: str
    group_name: str
    created_by: str
    token: str
    invitation_url: str  # Full URL with token

    max_uses: Optional[int]
    current_uses: int
    expires_at: Optional[int]
    status: str
    note: Optional[str]

    created_at: int
    updated_at: int


class InvitationValidationResponse(BaseModel):
    """Response for invitation validation"""
    valid: bool
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    message: Optional[str] = None


############################
# Helper Functions
############################


def generate_invitation_token() -> str:
    """Generate a secure random token for invitation"""
    return secrets.token_urlsafe(32)


def format_invitation_response(
    invitation: InvitationModel,
    base_url: str = None
) -> InvitationResponse:
    """Format invitation with group details and full URL"""
    if base_url is None:
        base_url = FRONTEND_BASE_URL

    group = Groups.get_group_by_id(invitation.group_id)
    group_name = group.name if group else "Unknown Group"

    invitation_url = f"{base_url}/auth?invite={invitation.token}"

    return InvitationResponse(
        id=invitation.id,
        group_id=invitation.group_id,
        group_name=group_name,
        created_by=invitation.created_by,
        token=invitation.token,
        invitation_url=invitation_url,
        max_uses=invitation.max_uses,
        current_uses=invitation.current_uses,
        expires_at=invitation.expires_at,
        status=invitation.status,
        note=invitation.note,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at
    )


############################
# API Endpoints
############################


@router.post("/create", response_model=InvitationResponse)
async def create_invitation(
    request: CreateInvitationRequest,
    user=Depends(get_admin_or_manager_user)
):
    """
    Create a new invitation link for a group.

    Managers can only create invitations for groups they manage.
    Admins can create invitations for any group.
    """
    # Check permissions
    if not can_manage_group(user, request.group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create invitations for this group"
        )

    # Verify group exists
    group = Groups.get_group_by_id(request.group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {request.group_id} not found"
        )

    # Generate unique token
    token = generate_invitation_token()

    # Calculate expiration timestamp if specified
    expires_at = None
    if request.expires_in_hours:
        expires_at = int(time.time()) + (request.expires_in_hours * 3600)

    # Create invitation
    invitation = Invitations.insert_new_invitation(
        group_id=request.group_id,
        created_by=user.id,
        token=token,
        max_uses=request.max_uses,
        expires_at=expires_at,
        note=request.note
    )

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invitation"
        )

    logger.info(f"Invitation created by {user.id} for group {request.group_id}")

    return format_invitation_response(invitation)


@router.get("/group/{group_id}", response_model=list[InvitationResponse])
async def get_group_invitations(
    group_id: str,
    user=Depends(get_admin_or_manager_user)
):
    """
    Get all invitations for a specific group.

    Managers can only view invitations for groups they manage.
    """
    # Check permissions
    if not can_manage_group(user, group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view invitations for this group"
        )

    invitations = Invitations.get_invitations_by_group_id(group_id)

    return [format_invitation_response(inv) for inv in invitations]


@router.get("/list", response_model=list[InvitationResponse])
async def list_my_invitations(
    user=Depends(get_admin_or_manager_user)
):
    """
    Get all invitations created by or accessible to the current user.

    Managers see invitations for all groups they manage.
    Admins see all invitations.
    """
    managed_groups = get_managed_groups(user)

    if user.role == "admin":
        # Admin can see all invitations - get invitations for all groups
        all_invitations = []
        all_groups = Groups.get_groups()
        for group in all_groups:
            group_invitations = Invitations.get_invitations_by_group_id(group.id)
            all_invitations.extend(group_invitations)
        invitations = all_invitations
    else:
        # Manager sees invitations for their managed groups
        invitations = []
        for group_id in managed_groups:
            group_invitations = Invitations.get_invitations_by_group_id(group_id)
            invitations.extend(group_invitations)

    return [format_invitation_response(inv) for inv in invitations]


@router.post("/{invitation_id}/revoke")
async def revoke_invitation(
    invitation_id: str,
    user=Depends(get_admin_or_manager_user)
):
    """
    Revoke (disable) an invitation.

    Managers can only revoke invitations for groups they manage.
    """
    invitation = Invitations.get_invitation_by_id(invitation_id)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    # Check permissions
    if not can_manage_group(user, invitation.group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to revoke this invitation"
        )

    # Update status to disabled
    updated_invitation = Invitations.update_invitation_status(invitation_id, "disabled")

    if not updated_invitation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke invitation"
        )

    logger.info(f"Invitation {invitation_id} revoked by {user.id}")

    return {"success": True, "message": "Invitation revoked successfully"}


@router.delete("/{invitation_id}")
async def delete_invitation(
    invitation_id: str,
    user=Depends(get_admin_or_manager_user)
):
    """
    Permanently delete an invitation.

    Managers can only delete invitations for groups they manage.
    """
    invitation = Invitations.get_invitation_by_id(invitation_id)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    # Check permissions
    if not can_manage_group(user, invitation.group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this invitation"
        )

    # Delete invitation
    success = Invitations.delete_invitation_by_id(invitation_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete invitation"
        )

    logger.info(f"Invitation {invitation_id} deleted by {user.id}")

    return {"success": True, "message": "Invitation deleted successfully"}


@router.get("/validate/{token}", response_model=InvitationValidationResponse)
async def validate_invitation(token: str):
    """
    Validate an invitation token (public endpoint for signup page).

    Returns validation status and group information if valid.
    """
    invitation = Invitations.get_invitation_by_token(token)

    if not invitation:
        return InvitationValidationResponse(
            valid=False,
            message="Invalid invitation token"
        )

    # Check if invitation is valid
    if not Invitations.is_invitation_valid(token):
        reason = "expired" if invitation.status == "expired" else "disabled"
        if invitation.expires_at and invitation.expires_at < int(time.time()):
            reason = "expired (time)"
        if invitation.max_uses and invitation.current_uses >= invitation.max_uses:
            reason = "expired (max uses reached)"

        return InvitationValidationResponse(
            valid=False,
            message=f"This invitation is {reason}"
        )

    # Get group information
    group = Groups.get_group_by_id(invitation.group_id)

    return InvitationValidationResponse(
        valid=True,
        group_id=invitation.group_id,
        group_name=group.name if group else "Unknown Group",
        message="Invitation is valid"
    )
