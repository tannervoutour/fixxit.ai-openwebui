"""
PostgreSQL connection utilities for Supabase integration
Handles parsing of psql connection strings and secure connection management
"""

import re
import asyncio
import asyncpg
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet
import os
import base64
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class PostgreSQLConnectionManager:
    """Manages PostgreSQL connections for group-based database access"""
    
    def __init__(self):
        self._connection_pools: Dict[str, asyncpg.Pool] = {}
        self._encryption_key = self._get_or_create_encryption_key()
    
    def _get_or_create_encryption_key(self) -> Fernet:
        """Get or create encryption key for storing database passwords"""
        key_env = os.getenv("DATABASE_PASSWORD_ENCRYPTION_KEY")
        
        if key_env:
            try:
                key = base64.urlsafe_b64decode(key_env.encode())
                return Fernet(key)
            except Exception as e:
                logger.warning(f"Invalid encryption key in environment: {e}")
        
        # Generate new key if none exists
        key = Fernet.generate_key()
        key_b64 = base64.urlsafe_b64encode(key).decode()
        logger.warning(f"Generated new encryption key. Set DATABASE_PASSWORD_ENCRYPTION_KEY={key_b64}")
        return Fernet(key)
    
    def parse_psql_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """
        Parse psql connection string into connection parameters
        
        Args:
            connection_string: psql command like "psql -h host -p port -d db -U user"
        
        Returns:
            Dict with connection parameters
        
        Raises:
            ValueError: If connection string format is invalid
        """
        # Clean up the connection string
        connection_string = connection_string.strip()
        
        # Pattern to match psql command with parameters
        pattern = r'psql\s+-h\s+(\S+)\s+-p\s+(\d+)\s+-d\s+(\S+)\s+-U\s+(\S+)'
        match = re.search(pattern, connection_string)
        
        if not match:
            raise ValueError(
                "Invalid psql connection string format. "
                "Expected: psql -h hostname -p port -d database -U username"
            )
        
        return {
            "host": match.group(1),
            "port": int(match.group(2)),
            "database": match.group(3),
            "user": match.group(4)
        }
    
    def encrypt_password(self, password: str) -> str:
        """Encrypt password for secure storage"""
        if not password:
            return ""
        return self._encryption_key.encrypt(password.encode()).decode()
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password for use in connections"""
        if not encrypted_password:
            return ""
        try:
            return self._encryption_key.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt password: {e}")
            raise ValueError("Failed to decrypt database password")
    
    def create_connection_config(
        self, 
        connection_string: str, 
        password: str
    ) -> Dict[str, Any]:
        """
        Create connection configuration from psql string and password
        
        Args:
            connection_string: psql command string
            password: Database password (will be encrypted)
        
        Returns:
            Dict with connection config including encrypted password
        """
        config = self.parse_psql_connection_string(connection_string)
        config["password"] = self.encrypt_password(password)
        config["ssl"] = True  # Default to SSL for Supabase
        return config
    
    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """
        Test database connection with given configuration
        
        Args:
            config: Connection configuration dict
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create connection parameters
            conn_params = {
                "host": config["host"],
                "port": config["port"],
                "database": config["database"],
                "user": config["user"],
                "password": self.decrypt_password(config["password"]),
                "ssl": config.get("ssl", True)
            }
            
            # Test connection
            conn = await asyncpg.connect(**conn_params)
            await conn.execute("SELECT 1")
            await conn.close()
            
            logger.info(f"Database connection test successful for {config['host']}")
            return True
            
        except Exception as e:
            logger.error(f"Database connection test failed for {config['host']}: {e}")
            return False
    
    async def get_connection_pool(self, group_id: str, config: Dict[str, Any]) -> Optional[asyncpg.Pool]:
        """
        Get or create connection pool for group database
        
        Args:
            group_id: Group identifier
            config: Database connection configuration
        
        Returns:
            Connection pool or None if failed
        """
        if group_id in self._connection_pools:
            return self._connection_pools[group_id]
        
        try:
            # Create connection parameters
            conn_params = {
                "host": config["host"],
                "port": config["port"],
                "database": config["database"],
                "user": config["user"],
                "password": self.decrypt_password(config["password"]),
                "ssl": config.get("ssl", True),
                "min_size": 1,
                "max_size": 5,  # Limit concurrent connections
                "command_timeout": 30
            }
            
            # Create connection pool
            pool = await asyncpg.create_pool(**conn_params)
            self._connection_pools[group_id] = pool
            
            logger.info(f"Created connection pool for group {group_id}")
            return pool
            
        except Exception as e:
            logger.error(f"Failed to create connection pool for group {group_id}: {e}")
            return None
    
    @asynccontextmanager
    async def get_connection(self, group_id: str, config: Dict[str, Any]):
        """
        Context manager to get database connection for group
        
        Usage:
            async with manager.get_connection(group_id, config) as conn:
                result = await conn.fetch("SELECT * FROM logs")
        """
        pool = await self.get_connection_pool(group_id, config)
        if not pool:
            raise ConnectionError(f"Failed to get connection pool for group {group_id}")
        
        conn = await pool.acquire()
        try:
            yield conn
        finally:
            await pool.release(conn)
    
    async def close_pool(self, group_id: str):
        """Close connection pool for specific group"""
        if group_id in self._connection_pools:
            await self._connection_pools[group_id].close()
            del self._connection_pools[group_id]
            logger.info(f"Closed connection pool for group {group_id}")
    
    async def close_all_pools(self):
        """Close all connection pools"""
        for group_id, pool in self._connection_pools.items():
            try:
                await pool.close()
                logger.info(f"Closed connection pool for group {group_id}")
            except Exception as e:
                logger.error(f"Error closing pool for group {group_id}: {e}")
        
        self._connection_pools.clear()

# Global connection manager instance
postgres_manager = PostgreSQLConnectionManager()


def parse_psql_connection_string(connection_string: str) -> Dict[str, Any]:
    """Convenience function for parsing connection strings"""
    return postgres_manager.parse_psql_connection_string(connection_string)


async def test_database_connection(connection_string: str, password: str) -> bool:
    """
    Test database connection from psql string and password
    
    Args:
        connection_string: psql command string
        password: Database password
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        config = postgres_manager.create_connection_config(connection_string, password)
        return await postgres_manager.test_connection(config)
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False