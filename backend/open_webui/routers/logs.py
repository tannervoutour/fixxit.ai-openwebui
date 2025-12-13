"""
Logs management router for Supabase integration
Handles CRUD operations for external logs storage with group-based access control
"""

import logging
import time
import uuid
import json
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
    insight_title: str
    insight_content: str
    user_name: str
    created_at: str
    updated_at: str
    source: str
    log_type: str
    activation_status: str
    verified: bool
    problem_category: Optional[str] = None
    root_cause: Optional[str] = None
    solution_steps: Optional[List[str]] = None
    tools_required: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    equipment_group: Optional[List[str]] = None
    notes: Optional[str] = None
    business_impact: Optional[str] = None
    reusability_score: Optional[float] = None
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
            try:
                return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                return None
        return None
    
    return LogResponse(
        id=log_data.get("id"),
        insight_title=log_data.get("insight_title", ""),
        insight_content=log_data.get("insight_content", ""),
        user_name=log_data.get("user_name", ""),
        created_at=safe_datetime_to_string(log_data.get("created_at")),
        updated_at=safe_datetime_to_string(log_data.get("updated_at")),
        source=log_data.get("source", ""),
        log_type=log_data.get("log_type", ""),
        activation_status=log_data.get("activation_status", ""),
        verified=log_data.get("verified", False),
        problem_category=log_data.get("problem_category"),
        root_cause=log_data.get("root_cause"),
        solution_steps=safe_json_parse(log_data.get("solution_steps")),
        tools_required=safe_json_parse(log_data.get("tools_required")),
        tags=safe_json_parse(log_data.get("tags")),
        equipment_group=safe_json_parse(log_data.get("equipment_group")),
        notes=log_data.get("notes"),
        business_impact=log_data.get("business_impact"),
        reusability_score=log_data.get("reusability_score"),
        source_group_name=group_name,
        source_group_id=group_id
    )

def create_log_entry_data(request: LogCreationRequest, user: UserModel) -> dict:
    """Create log entry dictionary from request and user context"""
    now = datetime.utcnow()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S.%f+00")
    
    return {
        # Auto-generated fields (as per user specifications)
        "source": "log_modal",                    # Column 3
        "verified": False,                        # Column 4
        "verification_method": None,              # Column 5
        "ai_confidence_score": None,              # Column 6
        "log_type": "user_generated",             # Column 7
        "activation_status": "Inactive",          # Column 9
        "created_at": timestamp_str,              # Column 10
        "updated_at": timestamp_str,              # Column 11
        "verified_at": None,                      # Column 12
        "verified_by": None,                      # Column 13
        "ai_model": None,                         # Column 16
        "diagram_referenced": None,               # Column 21
        "spare_parts_mentioned": None,            # Column 22
        "verification_confidence": None,          # Column 23
        "session_id": None,                       # Column 2 - not necessary per user
        
        # User context
        "user_name": user.name,                   # From OpenWebUI user
        
        # User input fields
        "insight_title": request.insight_title,          # Column 14
        "insight_content": request.insight_content,      # Column 15
        "problem_category": request.problem_category,    # Column 17
        "root_cause": request.root_cause,               # Column 18
        "solution_steps": request.solution_steps,       # Column 19
        "tools_required": request.tools_required,       # Column 20
        "tags": request.tags,                           # Column 24
        "equipment_group": request.equipment_group,      # Column 25
        "notes": request.notes,                         # Column 8
    }

############################
# API Endpoints
############################

@router.get("/", response_model=LogsListResponse)
async def get_logs(
    user=Depends(get_verified_user),
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
        filter_params = {"member_id": user.id} if user.role != "admin" else {}
        user_groups = Groups.get_groups(filter=filter_params)
        
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
                    query = "SELECT * FROM logs WHERE activation_status != 'deleted'"
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
        user_groups = Groups.get_groups_by_member_id(user.id)
        user_group_ids = [g.id for g in user_groups]
        
        if user.role != "admin" and group_id not in user_group_ids:
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
        filter_params = {"member_id": user.id} if user.role != "admin" else {}
        user_groups = Groups.get_groups(filter=filter_params)
        
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
    search: Optional[str] = Query(None, description="Search equipment by name")
):
    """Get equipment groups from user's accessible group databases for dropdown"""
    try:
        # Get user's groups with database configuration
        filter_params = {"member_id": user.id} if user.role != "admin" else {}
        user_groups = Groups.get_groups(filter=filter_params)
        
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