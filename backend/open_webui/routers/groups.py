import os
import time
from pathlib import Path
from typing import Optional
import logging

from open_webui.models.users import Users, UserInfoResponse
from open_webui.models.groups import (
    Groups,
    GroupForm,
    GroupUpdateForm,
    GroupResponse,
    UserIdsForm,
)

from open_webui.config import CACHE_DIR
from open_webui.constants import ERROR_MESSAGES
from fastapi import APIRouter, Depends, HTTPException, Request, status

from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.postgres_connection import postgres_manager, test_database_connection
from open_webui.env import SRC_LOG_LEVELS
from pydantic import BaseModel


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

router = APIRouter()

############################
# GetFunctions
############################


@router.get("/", response_model=list[GroupResponse])
async def get_groups(share: Optional[bool] = None, user=Depends(get_verified_user)):

    filter = {}
    if user.role != "admin":
        filter["member_id"] = user.id

    if share is not None:
        filter["share"] = share

    groups = Groups.get_groups(filter=filter)

    return groups


############################
# CreateNewGroup
############################


@router.post("/create", response_model=Optional[GroupResponse])
async def create_new_group(form_data: GroupForm, user=Depends(get_admin_user)):
    try:
        group = Groups.insert_new_group(user.id, form_data)
        if group:
            return GroupResponse(
                **group.model_dump(),
                member_count=Groups.get_group_member_count_by_id(group.id),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error creating group"),
            )
    except Exception as e:
        log.exception(f"Error creating a new group: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# GetGroupById
############################


@router.get("/id/{id}", response_model=Optional[GroupResponse])
async def get_group_by_id(id: str, user=Depends(get_admin_user)):
    group = Groups.get_group_by_id(id)
    if group:
        return GroupResponse(
            **group.model_dump(),
            member_count=Groups.get_group_member_count_by_id(group.id),
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# ExportGroupById
############################


class GroupExportResponse(GroupResponse):
    user_ids: list[str] = []
    pass


@router.get("/id/{id}/export", response_model=Optional[GroupExportResponse])
async def export_group_by_id(id: str, user=Depends(get_admin_user)):
    group = Groups.get_group_by_id(id)
    if group:
        return GroupExportResponse(
            **group.model_dump(),
            member_count=Groups.get_group_member_count_by_id(group.id),
            user_ids=Groups.get_group_user_ids_by_id(group.id),
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# GetUsersInGroupById
############################


@router.post("/id/{id}/users", response_model=list[UserInfoResponse])
async def get_users_in_group(id: str, user=Depends(get_admin_user)):
    try:
        users = Users.get_users_by_group_id(id)
        return users
    except Exception as e:
        log.exception(f"Error adding users to group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# UpdateGroupById
############################


@router.post("/id/{id}/update", response_model=Optional[GroupResponse])
async def update_group_by_id(
    id: str, form_data: GroupUpdateForm, user=Depends(get_admin_user)
):
    try:
        group = Groups.update_group_by_id(id, form_data)
        if group:
            return GroupResponse(
                **group.model_dump(),
                member_count=Groups.get_group_member_count_by_id(group.id),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error updating group"),
            )
    except Exception as e:
        log.exception(f"Error updating group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# AddUserToGroupByUserIdAndGroupId
############################


@router.post("/id/{id}/users/add", response_model=Optional[GroupResponse])
async def add_user_to_group(
    id: str, form_data: UserIdsForm, user=Depends(get_admin_user)
):
    try:
        if form_data.user_ids:
            form_data.user_ids = Users.get_valid_user_ids(form_data.user_ids)

        group = Groups.add_users_to_group(id, form_data.user_ids)
        if group:
            return GroupResponse(
                **group.model_dump(),
                member_count=Groups.get_group_member_count_by_id(group.id),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error adding users to group"),
            )
    except Exception as e:
        log.exception(f"Error adding users to group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


@router.post("/id/{id}/users/remove", response_model=Optional[GroupResponse])
async def remove_users_from_group(
    id: str, form_data: UserIdsForm, user=Depends(get_admin_user)
):
    try:
        group = Groups.remove_users_from_group(id, form_data.user_ids)
        if group:
            return GroupResponse(
                **group.model_dump(),
                member_count=Groups.get_group_member_count_by_id(group.id),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error removing users from group"),
            )
    except Exception as e:
        log.exception(f"Error removing users from group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# DeleteGroupById
############################


@router.delete("/id/{id}/delete", response_model=bool)
async def delete_group_by_id(id: str, user=Depends(get_admin_user)):
    try:
        result = Groups.delete_group_by_id(id)
        if result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error deleting group"),
            )
    except Exception as e:
        log.exception(f"Error deleting group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# Database Configuration
############################

class DatabaseConfigForm(BaseModel):
    connection_string: str
    password: str
    enabled: bool = True

class DatabaseConfigResponse(BaseModel):
    enabled: bool
    connection: dict
    test_status: Optional[str] = None

@router.post("/id/{id}/database/configure", response_model=Optional[GroupResponse])
async def configure_group_database(
    id: str, 
    config_form: DatabaseConfigForm, 
    user=Depends(get_admin_user)
):
    """Configure database connection for a group (admin only)"""
    try:
        # Get existing group
        group = Groups.get_group_by_id(id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.DEFAULT("Group not found"),
            )
        
        # Parse and validate connection string
        try:
            connection_config = postgres_manager.create_connection_config(
                config_form.connection_string, 
                config_form.password
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT(f"Invalid connection string: {str(e)}"),
            )
        
        # Test connection if enabled
        if config_form.enabled:
            connection_test = await postgres_manager.test_connection(connection_config)
            if not connection_test:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.DEFAULT("Database connection test failed"),
                )
        
        # Update group data with database configuration
        group_data = group.data or {}
        group_data["database"] = {
            "enabled": config_form.enabled,
            "connection": connection_config,
            "configured_at": int(time.time()),
            "configured_by": user.id
        }
        
        log.info(f"Saving database config for group {id}: enabled={config_form.enabled}, group_data={group_data}")
        
        # Update group
        updated_group = Groups.update_group_by_id(
            id, 
            GroupUpdateForm(
                name=group.name,
                description=group.description,
                data=group_data
            )
        )
        
        if updated_group:
            log.info(f"Database configured for group {id} by user {user.id}")
            log.info(f"Updated group data: {updated_group.data}")
            return GroupResponse(
                **updated_group.model_dump(),
                member_count=Groups.get_group_member_count_by_id(updated_group.id),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error updating group database configuration"),
            )
            
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error configuring database for group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(f"Internal server error: {str(e)}"),
        )


@router.get("/id/{id}/database", response_model=Optional[DatabaseConfigResponse])
async def get_group_database_config(id: str, user=Depends(get_admin_user)):
    """Get database configuration for a group (admin only)"""
    try:
        group = Groups.get_group_by_id(id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.DEFAULT("Group not found"),
            )
        
        if not group.data or "database" not in group.data:
            log.info(f"Group {id} has no database config in data: {group.data}")
            return DatabaseConfigResponse(
                enabled=False,
                connection={}
            )
        
        db_config = group.data["database"]
        log.info(f"Group {id} database config: {db_config}")
        
        # Return config without sensitive password
        safe_connection = db_config["connection"].copy()
        if "password" in safe_connection:
            safe_connection["password"] = "***encrypted***"
        
        return DatabaseConfigResponse(
            enabled=db_config.get("enabled", False),
            connection=safe_connection
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error getting database config for group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(f"Internal server error: {str(e)}"),
        )


@router.post("/database/test", response_model=dict)
async def test_database_connection_endpoint(
    config_form: DatabaseConfigForm, 
    user=Depends(get_admin_user)
):
    """Test database connection without saving configuration"""
    try:
        # Test the connection
        success = await test_database_connection(
            config_form.connection_string, 
            config_form.password
        )
        
        return {
            "success": success,
            "message": "Connection successful" if success else "Connection failed"
        }
        
    except Exception as e:
        log.exception(f"Error testing database connection: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}"
        }


@router.get("/accessible-with-logs", response_model=list[dict])
async def get_accessible_groups_with_logs(user=Depends(get_verified_user)):
    """Get groups accessible to user that have database configuration enabled"""
    try:
        # Get user's groups
        filter_params = {"member_id": user.id} if user.role != "admin" else {}
        groups = Groups.get_groups(filter=filter_params)
        
        accessible_groups = []
        log.info(f"Checking {len(groups)} groups for user {user.id}")
        
        for group in groups:
            log.info(f"Group {group.id} ({group.name}): data={group.data}")
            if (group.data and 
                "database" in group.data and 
                group.data["database"].get("enabled", False)):
                
                # Test actual connection to verify credentials work
                db_config = group.data["database"].get("connection", {})
                connection_test_result = await postgres_manager.test_connection(db_config)
                log.info(f"Group {group.id} database connection test result: {connection_test_result}")
                
                if connection_test_result:
                    log.info(f"Group {group.id} has enabled database with working connection - adding to accessible groups")
                    accessible_groups.append({
                        "id": group.id,
                        "name": group.name,
                        "description": group.description
                    })
                else:
                    log.error(f"Group {group.id} has enabled database but connection failed")
                    # Still add to accessible groups so user can see the issue
                    accessible_groups.append({
                        "id": group.id,
                        "name": group.name,
                        "description": group.description + " (Connection Failed)"
                    })
            else:
                log.info(f"Group {group.id} does not have enabled database")
        
        log.info(f"Returning {len(accessible_groups)} accessible groups with logs")
        return accessible_groups
        
    except Exception as e:
        log.exception(f"Error getting accessible groups with logs for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(f"Internal server error: {str(e)}"),
        )
