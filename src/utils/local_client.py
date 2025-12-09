import asyncio
import logging
import os
import random
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents import Runner, function_tool
from agents.model_settings import ModelSettings
from agents_mcp import Agent, RunnerContext
from pydantic import BaseModel, Field

from src.utils.database_functions import (_describe_table, _list_tables,
                                          _read_query)

logger = logging.getLogger("ShieldyLogger")

class Local_Client:
    rail = None
    use_rail = False
    
    def __init__(self, api_key: str, rail):
        """
        Initializes the agent client with local tools.
        """
        os.environ['OPENAI_API_KEY'] = api_key
        Local_Client.rail = rail
        
    def call(self, system_instructions: str, messages: List[dict], model:str = "gpt-4", use_rail: bool = False) -> str:
        Local_Client.use_rail = use_rail
        try:
            response = asyncio.run(self._call(system_instructions, messages, model))
            return response
        except Exception as e:
            logger.info(f"Exception on tool call: '{e}'")
            return "Please try again."
    
    async def _call(self, system_instructions: str, messages: List[dict], model:str="gpt-4") -> str:
        agent = Agent(
            name="Chatbot Shieldy",
            instructions=system_instructions,
            tools=[self.list_tables, self.read_query, self.describe_table],
            # tool_use_behavior="stop_on_first_tool",
            # input_guardrails=[prompt_injection_guardrail],
            # output_guardrails=[sensitive_data_guardrail],
            model_settings=ModelSettings(tool_choice="auto"),
            model=model
        )
        result = await Runner.run(agent, input=messages)
        return str(result.final_output)
          
    @staticmethod
    @function_tool
    def list_tables() -> List[str]:
        """List all tables in the database.
    
        Returns:
            List of table names in the database
        """
        response = _list_tables()
        logger.info(f"List tables response: {response}")
        return response
            
    @function_tool
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
        response = str(_read_query(query, params, fetch_all, row_limit))
        if Local_Client.use_rail:
            response = Local_Client.rail.validate(response).validated_output

        logger.info(f"Read query response: {response}")
        return response

    @function_tool
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
        response = str(_describe_table(table_name))
        if Local_Client.use_rail:
            response = Local_Client.rail.validate(response).validated_output
        logger.info(f"Describe table response: {response}")
        return response