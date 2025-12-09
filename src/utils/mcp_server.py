from typing import Any, Dict, List, Optional

import streamlit as st
from database_functions import _describe_table, _list_tables, _read_query
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("SQLite Explorer",
    log_level="CRITICAL")

@mcp.tool()
def list_tables() -> List[str]:
    """List all tables in the database.
    
    Returns:
        List of table names in the database
    """
    return _list_tables()
        
@mcp.tool()
def read_query(
        query: str,
        params: Optional[List[str]] = None,
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
    return _read_query(query, params, fetch_all, row_limit)

@mcp.tool()
def describe_table(table_name: str) -> List[Dict[str, str]]:
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
    return _describe_table(table_name)
        
if __name__ == "__main__":
    mcp.run(transport="sse")