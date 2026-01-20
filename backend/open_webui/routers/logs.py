"""
Logs management router for Supabase integration
Handles CRUD operations for external logs storage with group-based access control
"""

import logging
import time
import uuid
import json
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.utils.postgres_connection import postgres_manager
from open_webui.models.groups import Groups
from open_webui.models.users import UserModel
from open_webui.constants import ERROR_MESSAGES

logger = logging.getLogger(__name__)

router = APIRouter()

############################
# Request/Response Models
############################

class LogCreationRequest(BaseModel):
    """Request model for creating new logs"""
    # Required fields
    insight_title: str = Field(..., max_length=500, description="Brief descriptive title")
    insight_content: str = Field(..., description="Detailed log content")
    
    # Optional fields
    problem_category: Optional[str] = Field(None, max_length=200, description="Issue category")
    root_cause: Optional[str] = Field(None, description="Root cause analysis")
    solution_steps: Optional[List[str]] = Field(None, description="Step-by-step solution")
    tools_required: Optional[List[str]] = Field(None, description="Tools used or required")
    tags: Optional[List[str]] = Field(None, max_items=3, description="Classification tags (max 3)")
    equipment_group: Optional[List[str]] = Field(None, description="Equipment involved")
    notes: Optional[str] = Field(None, description="Additional notes")

class LogResponse(BaseModel):
    """Response model for log data"""
    id: int
    session_id: str
    insight_title: str
    insight_content: str
    user_name: str
    created_at: str
    updated_at: str
    source: str
    log_type: str
    activation_status: str
    verified: bool
    verification_method: Optional[str] = None
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    ai_generated_at: Optional[str] = None
    ai_model: Optional[str] = None
    ai_confidence_score: Optional[float] = None
    problem_category: Optional[str] = None
    root_cause: Optional[str] = None
    solution_steps: Optional[List[str]] = None
    tools_required: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    equipment_group: Optional[List[str]] = None
    notes: Optional[str] = None
    business_impact: Optional[str] = None
    # Group context (added by API)
    source_group_name: Optional[str] = None
    source_group_id: Optional[str] = None

class LogsListResponse(BaseModel):
    """Response model for logs list"""
    logs: List[LogResponse]
    total: int
    has_more: bool
    categories: List[str] = []  # Available categories for filtering
    debug_info: Optional[List[str]] = []  # Debug information for troubleshooting

class EquipmentGroupResponse(BaseModel):
    """Response model for equipment groups"""
    id: int
    conventional_name: str
    model_numbers: List[str]
    aliases: List[str]

############################
# Helper Functions
############################

async def get_group_database_connection(group_id: str):
    """Get database connection configuration for a group"""
    group = Groups.get_group_by_id(group_id)
    if not group or not group.data or "database" not in group.data:
        return None
    
    db_config = group.data["database"]
    if not db_config.get("enabled", False):
        return None
    
    return db_config["connection"]

def format_log_entry(log_data: dict, group_name: str, group_id: str) -> LogResponse:
    """Format database log entry into response model"""
    
    def safe_datetime_to_string(dt_value):
        """Convert datetime object to string safely"""
        if dt_value is None:
            return ""
        if isinstance(dt_value, datetime):
            return dt_value.isoformat()
        return str(dt_value)
    
    def safe_json_parse(json_str):
        """Parse JSON string to list/dict safely"""
        if json_str is None:
            return None
        if isinstance(json_str, (list, dict)):
            return json_str
        if isinstance(json_str, str):
            # First try to parse as JSON
            try:
                parsed = json.loads(json_str)
                # Ensure it's a list
                if isinstance(parsed, list):
                    return parsed
                # If it's a single value, wrap it in a list
                return [parsed] if parsed else None
            except (json.JSONDecodeError, ValueError):
                # If JSON parsing fails, check if it looks like a numbered list
                if re.match(r'^\d+\.', json_str.strip()):
                    # Split by numbered list pattern (1. 2. 3. etc)
                    items = re.split(r'\d+\.\s*', json_str)
                    return [item.strip() for item in items if item.strip()]
                # Otherwise, treat as comma-separated string
                return [item.strip() for item in json_str.split(',') if item.strip()]
        return None
    
    return LogResponse(
        id=log_data.get("id"),
        session_id=log_data.get("session_id", ""),
        insight_title=log_data.get("insight_title", ""),
        insight_content=log_data.get("insight_content", ""),
        user_name=log_data.get("user_name", ""),
        created_at=safe_datetime_to_string(log_data.get("created_at")),
        updated_at=safe_datetime_to_string(log_data.get("updated_at")),
        source=log_data.get("source", ""),
        log_type=log_data.get("log_type", ""),
        activation_status=log_data.get("activation_status", ""),
        verified=log_data.get("verified", False),
        verification_method=log_data.get("verification_method"),
        verified_at=safe_datetime_to_string(log_data.get("verified_at")),
        verified_by=log_data.get("verified_by"),
        ai_generated_at=safe_datetime_to_string(log_data.get("ai_generated_at")),
        ai_model=log_data.get("ai_model"),
        ai_confidence_score=log_data.get("ai_confidence_score"),
        problem_category=log_data.get("problem_category"),
        root_cause=log_data.get("root_cause"),
        solution_steps=safe_json_parse(log_data.get("solution_steps")),
        tools_required=safe_json_parse(log_data.get("tools_required")),
        tags=safe_json_parse(log_data.get("tags")),
        equipment_group=safe_json_parse(log_data.get("equipment_group")),
        notes=log_data.get("notes"),
        business_impact=log_data.get("business_impact"),
        source_group_name=group_name,
        source_group_id=group_id
    )

def create_log_entry_data(request: LogCreationRequest, user: UserModel) -> dict:
    """Create log entry dictionary from request and user context"""
    now = datetime.utcnow()

    # Generate a session ID (required field, NOT NULL in schema)
    session_id = f"manual_{uuid.uuid4().hex[:16]}"

    return {
        # Required fields
        "session_id": session_id,                       # Required, NOT NULL
        "user_name": user.name,                         # Required, NOT NULL
        "insight_title": request.insight_title,         # Required, NOT NULL
        "insight_content": request.insight_content,     # Required, NOT NULL

        # Auto-generated fields
        "source": "log_modal",
        "log_type": "user_generated",
        "activation_status": "active",
        "verified": False,
        "verification_method": "manual",

        # Timestamps (let database handle defaults, but we can set them)
        "created_at": now,
        "updated_at": now,
        "ai_generated_at": None,

        # Optional verification fields
        "verified_at": None,
        "verified_by": None,
        "ai_model": None,
        "ai_confidence_score": None,

        # User input fields (JSONB fields should be lists/dicts, not strings)
        "problem_category": request.problem_category,
        "root_cause": request.root_cause,
        "solution_steps": json.dumps(request.solution_steps) if request.solution_steps else None,
        "tools_required": json.dumps(request.tools_required) if request.tools_required else None,
        "tags": json.dumps(request.tags) if request.tags else None,
        "equipment_group": json.dumps(request.equipment_group) if request.equipment_group else None,
        "notes": request.notes,
        "business_impact": None,  # Not in request model, but exists in schema
    }

############################
# API Endpoints
############################

@router.get("/", response_model=LogsListResponse)
async def get_logs(
    user=Depends(get_verified_user),
    group_id: Optional[str] = Query(None, description="Filter by specific group"),
    category: Optional[str] = Query(None, description="Filter by problem category"),
    business_impact: Optional[str] = Query(None, description="Filter by business impact"),
    verified: Optional[bool] = Query(None, description="Filter by verification status"),
    equipment: Optional[str] = Query(None, description="Filter by equipment"),
    user_filter: Optional[str] = Query(None, description="Filter by user name"),
    title_search: Optional[str] = Query(None, description="Search in log titles"),
    date_after: Optional[str] = Query(None, description="Filter logs after this date"),
    date_before: Optional[str] = Query(None, description="Filter logs before this date"),
    limit: int = Query(50, ge=1, le=200, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_desc: bool = Query(True, description="Sort in descending order")
):
    """Get logs accessible to user based on group membership with filtering and sorting"""

    # Add debug info to response headers for frontend visibility
    debug_info = []

    try:
        # Get user's groups with database configuration
        if user.role == "admin":
            # Admins see all groups
            user_groups = Groups.get_groups(filter={})
        elif user.role == "manager":
            # Managers see their managed groups
            if user.managed_groups:
                user_groups = [Groups.get_group_by_id(gid) for gid in user.managed_groups]
                user_groups = [g for g in user_groups if g is not None]
            else:
                user_groups = []
        else:
            # Regular users see groups they are members of
            user_groups = Groups.get_groups(filter={"member_id": user.id})

        # Filter to specific group if requested
        if group_id:
            user_groups = [g for g in user_groups if g.id == group_id]
            debug_info.append(f"Filtering to specific group: {group_id}")
            logger.info(f"get_logs: Filtering to specific group: {group_id}")

        debug_info.append(f"User {user.id} has {len(user_groups)} groups")
        logger.info(f"get_logs: User {user.id} has {len(user_groups)} groups")
        
        all_logs = []
        all_categories = set()
        
        # Fetch logs from each group's database
        for group in user_groups:
            debug_info.append(f"Processing group {group.id} ({group.name})")
            logger.info(f"get_logs: Processing group {group.id} ({group.name})")
            db_config = await get_group_database_connection(group.id)
            if not db_config:
                debug_info.append(f"Group {group.id} has no database configuration")
                logger.info(f"get_logs: Group {group.id} has no database configuration")
                continue
            
            debug_info.append(f"Group {group.id} has database configuration, querying logs")
            logger.info(f"get_logs: Group {group.id} has database configuration, querying logs")
            
            try:
                async with postgres_manager.get_connection(group.id, db_config) as conn:
                    # Build query with filters
                    # Explicitly select columns to avoid issues with the embedding vector column
                    query = """
                    SELECT id, session_id, user_name, insight_title, insight_content,
                           ai_generated_at, ai_model, ai_confidence_score, equipment_group,
                           problem_category, root_cause, solution_steps, tools_required,
                           verified, verification_method, verified_at, verified_by,
                           business_impact, tags, source, log_type, notes,
                           activation_status, created_at, updated_at
                    FROM logs
                    WHERE activation_status != 'deleted'
                    """
                    query_params = []
                    
                    # Apply filters
                    if category:
                        query += " AND problem_category = $" + str(len(query_params) + 1)
                        query_params.append(category)
                    
                    if business_impact:
                        query += " AND business_impact = $" + str(len(query_params) + 1)
                        query_params.append(business_impact)
                    
                    if verified is not None:
                        query += " AND verified = $" + str(len(query_params) + 1)
                        query_params.append(verified)
                    
                    if equipment:
                        query += " AND equipment_group @> $" + str(len(query_params) + 1)
                        query_params.append(f'["{equipment}"]')
                    
                    if user_filter:
                        query += " AND LOWER(user_name) LIKE LOWER($" + str(len(query_params) + 1) + ")"
                        query_params.append(f"%{user_filter}%")
                    
                    if title_search:
                        query += " AND LOWER(insight_title) LIKE LOWER($" + str(len(query_params) + 1) + ")"
                        query_params.append(f"%{title_search}%")
                    
                    if date_after:
                        # Convert string date to Python date object for asyncpg
                        date_after_obj = datetime.strptime(date_after, "%Y-%m-%d").date()
                        query += " AND created_at::date >= $" + str(len(query_params) + 1)
                        query_params.append(date_after_obj)
                    
                    if date_before:
                        # Convert string date to Python date object for asyncpg
                        date_before_obj = datetime.strptime(date_before, "%Y-%m-%d").date()
                        query += " AND created_at::date <= $" + str(len(query_params) + 1)
                        query_params.append(date_before_obj)
                    
                    # Add sorting
                    valid_sort_fields = ["created_at", "updated_at", "insight_title", "problem_category", "user_name"]
                    if sort_by not in valid_sort_fields:
                        sort_by = "created_at"
                    
                    query += f" ORDER BY {sort_by}"
                    if sort_desc:
                        query += " DESC"
                    
                    
                    # Add pagination
                    query += " LIMIT $" + str(len(query_params) + 1)
                    query_params.append(limit)
                    
                    if offset > 0:
                        query += " OFFSET $" + str(len(query_params) + 1)
                        query_params.append(offset)
                    
                    # Execute query
                    logger.info(f"get_logs: Executing query: {query} with params: {query_params}")
                    rows = await conn.fetch(query, *query_params)
                    debug_info.append(f"Query returned {len(rows)} logs from group {group.id}")
                    logger.info(f"get_logs: Query returned {len(rows)} logs from group {group.id}")
                    
                    # Format results
                    for row in rows:
                        log_dict = dict(row)
                        formatted_log = format_log_entry(log_dict, group.name, group.id)
                        all_logs.append(formatted_log)
                        
                        # Collect categories
                        if log_dict.get("problem_category"):
                            all_categories.add(log_dict["problem_category"])
                
            except Exception as e:
                logger.error(f"Error fetching logs from group {group.name} ({group.id}): {e}")
                continue
        
        # Sort combined results if multiple groups
        if len([g for g in user_groups if Groups.get_group_by_id(g.id)]) > 1:
            reverse = sort_desc
            all_logs.sort(key=lambda x: getattr(x, sort_by, ""), reverse=reverse)
        
        # Apply final pagination if needed
        total_logs = len(all_logs)
        if len(all_logs) > limit:
            all_logs = all_logs[:limit]
        
        return LogsListResponse(
            logs=all_logs,
            total=total_logs,
            has_more=total_logs > limit,
            categories=sorted(list(all_categories)),
            debug_info=debug_info
        )
        
    except Exception as e:
        logger.exception(f"Error getting logs for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(f"Error retrieving logs: {str(e)}"),
        )

@router.post("/", response_model=dict)
async def create_log(
    log_data: LogCreationRequest,
    group_id: str = Query(..., description="Target group ID"),
    user=Depends(get_verified_user)
):
    """Create new log entry in group's database"""
    try:
        # Verify user access to group
        if user.role == "admin":
            # Admins have access to all groups
            pass
        elif user.role == "manager":
            # Managers have access to their managed groups
            if not user.managed_groups or group_id not in user.managed_groups:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ERROR_MESSAGES.DEFAULT("Access denied to group"),
                )
        else:
            # Regular users have access to groups they are members of
            user_groups = Groups.get_groups_by_member_id(user.id)
            user_group_ids = [g.id for g in user_groups]
            if group_id not in user_group_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ERROR_MESSAGES.DEFAULT("Access denied to group"),
                )
        
        # Get database configuration
        db_config = await get_group_database_connection(group_id)
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.DEFAULT("Database not configured for group"),
            )
        
        # Create log entry data
        log_entry = create_log_entry_data(log_data, user)
        
        # Insert into database
        async with postgres_manager.get_connection(group_id, db_config) as conn:
            # Prepare insert query
            columns = list(log_entry.keys())
            placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
            query = f"INSERT INTO logs ({', '.join(columns)}) VALUES ({placeholders}) RETURNING id"
            
            # Execute insert
            result = await conn.fetchrow(query, *log_entry.values())
            
            if result:
                logger.info(f"Created log entry {result['id']} in group {group_id} by user {user.id}")
                return {
                    "success": True,
                    "log_id": result["id"],
                    "message": "Log created successfully"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ERROR_MESSAGES.DEFAULT("Failed to create log entry"),
                )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error creating log in group {group_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(f"Error creating log: {str(e)}"),
        )

@router.get("/categories", response_model=List[str])
async def get_problem_categories(user=Depends(get_verified_user)):
    """Get unique problem categories from user's accessible group databases"""
    try:
        # Get user's groups with database configuration
        if user.role == "admin":
            # Admins see all groups
            user_groups = Groups.get_groups(filter={})
        elif user.role == "manager":
            # Managers see their managed groups
            if user.managed_groups:
                user_groups = [Groups.get_group_by_id(gid) for gid in user.managed_groups]
                user_groups = [g for g in user_groups if g is not None]
            else:
                user_groups = []
        else:
            # Regular users see groups they are members of
            user_groups = Groups.get_groups(filter={"member_id": user.id})

        all_categories = set()
        
        # Fetch categories from each group's database
        for group in user_groups:
            db_config = await get_group_database_connection(group.id)
            if not db_config:
                continue
            
            try:
                async with postgres_manager.get_connection(group.id, db_config) as conn:
                    query = """
                    SELECT DISTINCT problem_category 
                    FROM logs 
                    WHERE problem_category IS NOT NULL 
                    AND activation_status != 'deleted'
                    ORDER BY problem_category
                    """
                    
                    rows = await conn.fetch(query)
                    for row in rows:
                        if row["problem_category"]:
                            all_categories.add(row["problem_category"])
                
            except Exception as e:
                logger.error(f"Error fetching categories from group {group.name}: {e}")
                continue
        
        return sorted(list(all_categories))
        
    except Exception as e:
        logger.exception(f"Error getting problem categories for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(f"Error retrieving categories: {str(e)}"),
        )

@router.get("/equipment-groups", response_model=List[EquipmentGroupResponse])
async def get_equipment_groups(
    user=Depends(get_verified_user),
    group_id: Optional[str] = Query(None, description="Filter by specific group"),
    search: Optional[str] = Query(None, description="Search equipment by name")
):
    """Get equipment groups from user's accessible group databases for dropdown"""
    try:
        # Get user's groups with database configuration
        if group_id:
            # Fetch from specific group only
            group = Groups.get_group_by_id(group_id)
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Group not found"
                )

            # Verify user has access to this group
            has_access = False
            if user.role == "admin":
                has_access = True
            elif user.role == "manager" and user.managed_groups and group_id in user.managed_groups:
                has_access = True
            else:
                # Check if user is a member of the group
                group_user_ids = Groups.get_group_user_ids_by_id(group_id)
                if group_user_ids and user.id in group_user_ids:
                    has_access = True

            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this group"
                )

            user_groups = [group]
        else:
            # Original logic - fetch from all accessible groups
            if user.role == "admin":
                # Admins see all groups
                user_groups = Groups.get_groups(filter={})
            elif user.role == "manager":
                # Managers see their managed groups
                if user.managed_groups:
                    user_groups = [Groups.get_group_by_id(gid) for gid in user.managed_groups]
                    user_groups = [g for g in user_groups if g is not None]
                else:
                    user_groups = []
            else:
                # Regular users see groups they are members of
                user_groups = Groups.get_groups(filter={"member_id": user.id})

        all_equipment = {}  # Use dict to avoid duplicates by conventional_name
        
        # Fetch equipment from each group's database
        for group in user_groups:
            db_config = await get_group_database_connection(group.id)
            if not db_config:
                continue
            
            try:
                async with postgres_manager.get_connection(group.id, db_config) as conn:
                    query = """
                    SELECT id, conventional_name, model_numbers, aliases
                    FROM equipment_groups 
                    WHERE activation_status = 'active'
                    """
                    query_params = []
                    
                    if search:
                        query += """ AND (
                            LOWER(conventional_name) LIKE LOWER($1) OR
                            EXISTS (
                                SELECT 1 FROM unnest(aliases) AS alias 
                                WHERE LOWER(alias) LIKE LOWER($1)
                            )
                        )"""
                        query_params.append(f"%{search}%")
                    
                    query += " ORDER BY conventional_name"
                    
                    rows = await conn.fetch(query, *query_params)
                    for row in rows:
                        equipment_key = row["conventional_name"]
                        if equipment_key not in all_equipment:
                            all_equipment[equipment_key] = EquipmentGroupResponse(
                                id=row["id"],
                                conventional_name=row["conventional_name"],
                                model_numbers=row["model_numbers"] or [],
                                aliases=row["aliases"] or []
                            )
                
            except Exception as e:
                logger.error(f"Error fetching equipment from group {group.name}: {e}")
                continue
        
        return list(all_equipment.values())
        
    except Exception as e:
        logger.exception(f"Error getting equipment groups for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(f"Error retrieving equipment groups: {str(e)}"),
        )