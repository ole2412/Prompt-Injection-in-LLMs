import asyncio
import logging
import os
import random
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.database_connection import SQLiteConnection

DB_PATH = Path(__file__).resolve().parent / ".." / ".." / "database" / "users.db"

logger = logging.getLogger("ShieldyLogger")


def init_database(emails: List[str]):
    if DB_PATH.exists():
        os.remove(DB_PATH)
    return SQLiteConnection(DB_PATH).setup_table(emails)

def _list_tables() -> List[str]:
    """List all tables in the database.
    
    Returns:
        List of table names in the database
    """
    # log the call
    logger.info("list_tables called")
    
    with SQLiteConnection(DB_PATH) as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            
            return [row['name'] for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.info(f"SQLite error: {str(e)}")
            return f"SQLite error: {str(e)}"
        
def _read_query(
    query: str,
    params: Optional[List[Any]] = None,
    fetch_all: bool = True,
    row_limit: int = 1000
) -> List[Dict[str, Any]]:
    """Execute a query on the database.
    
    Args:
        query: SELECT SQL query to execute
        params: Optional list of parameters for the query
        fetch_all: If True, fetches all results. If False, fetches one row.
        row_limit: Maximum number of rows to return (default 1000)
    
    Returns:
        List of dictionaries containing the query results
    """
    logger.info(f"read_query called with {query}")
    if not DB_PATH.exists():
        return f"Database not found at: {DB_PATH}"
    
    # Clean and validate the query
    query = query.strip()
    
    # Remove trailing semicolon if present
    if query.endswith(';'):
        query = query[:-1].strip()
    
    # Check for multiple statements by looking for semicolons not inside quotes
    def contains_multiple_statements(sql: str) -> bool:
        in_single_quote = False
        in_double_quote = False
        for char in sql:
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == ';' and not in_single_quote and not in_double_quote:
                return True
        return False
    
    if contains_multiple_statements(query):
        return "Multiple SQL statements are not allowed"
    
    # Validate query type (allowing common CTEs)
    query_lower = query.lower()
    if not any(query_lower.startswith(prefix) for prefix in ('select', 'with')):
        return "Only SELECT queries (including WITH clauses) are allowed for safety"
    
    params = params or []
    
    with SQLiteConnection(DB_PATH) as conn:
        cursor = conn.cursor()
        
        try:
            # Only add LIMIT if query doesn't already have one
            if 'limit' not in query_lower:
                query = f"{query} LIMIT {row_limit}"
            
            cursor.execute(query, params)
            
            if fetch_all:
                results = cursor.fetchall()
            else:
                results = [cursor.fetchone()]
                
            logger.info(f"Query executed: {query}")
            response = [dict(row) for row in results if row is not None]
            logger.info(f"Response is: {response}")
            return response
            
        except sqlite3.Error as e:
            logger.info(f"SQLite error: {str(e)}")
            return f"SQLite error: {str(e)}"

def _describe_table(table_name: str) -> List[Dict[str, str]]:
    """Get detailed information about a table's schema.
    
    Args:
        table_name: Name of the table to describe
        
    Returns:
        List of dictionaries containing column information:
        - name: Column name
        - type: Column data type
        - notnull: Whether the column can contain NULL values
        - dflt_value: Default value for the column
        - pk: Whether the column is part of the primary key
    """
    logger.info(f"describe_table called for table {table_name}")
    if not DB_PATH.exists():
        return f"Database not found at: {DB_PATH}"
    
    with SQLiteConnection(DB_PATH) as conn:
        cursor = conn.cursor()
        
        try:
            # Verify table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, [table_name])
            
            if not cursor.fetchone():
                return f"Table '{table_name}' does not exist"
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            response = [dict(row) for row in columns]
            logger.info(response)
            return response
            
        except sqlite3.Error as e:
            return f"SQLite error: {str(e)}"
        
        