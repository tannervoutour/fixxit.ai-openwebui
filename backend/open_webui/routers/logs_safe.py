"""
Safe logs router that handles missing dependencies gracefully
This provides basic endpoints that return appropriate error messages when dependencies are missing
"""

import logging
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()

# Check if PostgreSQL dependencies are available
POSTGRES_AVAILABLE = False
try:
    import asyncpg
    from open_webui.utils.postgres_connection import postgres_manager
    POSTGRES_AVAILABLE = True
    logger.info("PostgreSQL dependencies available - full logs functionality enabled")
except ImportError as e:
    logger.warning(f"PostgreSQL dependencies not available: {e}")
    logger.warning("Logs endpoints will return appropriate error messages")

@router.get("/")
async def get_logs():
    """Get logs endpoint with dependency check"""
    if not POSTGRES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Logs functionality requires PostgreSQL dependencies. Please install asyncpg and configure the database connection."
        )
    
    # Import the actual router only if dependencies are available
    try:
        from open_webui.routers.logs import get_logs_impl
        return await get_logs_impl()
    except Exception as e:
        logger.error(f"Error in logs implementation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logs service is currently unavailable"
        )

@router.post("/")
async def create_log():
    """Create log endpoint with dependency check"""
    if not POSTGRES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Logs functionality requires PostgreSQL dependencies. Please install asyncpg and configure the database connection."
        )
    
    try:
        from open_webui.routers.logs import create_log_impl
        return await create_log_impl()
    except Exception as e:
        logger.error(f"Error in logs implementation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logs service is currently unavailable"
        )

@router.get("/categories")
async def get_problem_categories():
    """Get problem categories endpoint with dependency check"""
    if not POSTGRES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Logs functionality requires PostgreSQL dependencies."
        )
    
    try:
        from open_webui.routers.logs import get_problem_categories_impl
        return await get_problem_categories_impl()
    except Exception as e:
        logger.error(f"Error in logs implementation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logs service is currently unavailable"
        )

@router.get("/equipment-groups")
async def get_equipment_groups():
    """Get equipment groups endpoint with dependency check"""
    if not POSTGRES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Logs functionality requires PostgreSQL dependencies."
        )
    
    try:
        from open_webui.routers.logs import get_equipment_groups_impl
        return await get_equipment_groups_impl()
    except Exception as e:
        logger.error(f"Error in logs implementation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logs service is currently unavailable"
        )

@router.get("/health")
async def logs_health_check() -> Dict[str, Any]:
    """Health check endpoint for logs functionality"""
    return {
        "status": "available" if POSTGRES_AVAILABLE else "unavailable",
        "postgresql_dependencies": POSTGRES_AVAILABLE,
        "message": "Logs functionality is ready" if POSTGRES_AVAILABLE else "PostgreSQL dependencies missing"
    }