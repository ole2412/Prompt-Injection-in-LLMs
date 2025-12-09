import asyncio
import atexit
import logging
import os
import shutil
import signal
import subprocess
import time
from typing import Any, List

import streamlit as st
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings

from src.utils.openai_utils import AssistantMessage, SystemMessage, UserMessage

logger = logging.getLogger("ShieldyLogger")

class MCP_Client:
    
    def __init__(self, api_key, rail):
        """
        Initializes the MCP_Client by starting the MCP server using uv.
        """
        OPENAI_API_KEY = api_key
        if rail is not None:
            logger.info("Tool rails are not supported with MCP yet")

        if not shutil.which("uv"):
            raise RuntimeError(
                "uv is not installed. Please install it: https://docs.astral.sh/uv/getting-started/installation/"
            )
        
        self.process: subprocess.Popen[Any] | None = None
        try:
            this_dir = os.path.dirname(os.path.abspath(__file__))
            server_file = os.path.join(this_dir, "mcp_server.py")
            self.process = subprocess.Popen(["uv", "run", server_file])
                        
            time.sleep(3)
            logger.info("mcp database server started...")

        except Exception as e:
            logger.info(f"Error on MCP init: {e}")
            self._terminate_process()
            exit(1)         

    async def _run(self, system_instructions: str, mcp_server: MCPServer, messages: List[dict], model) -> str:
        """
        Runs the agent with the given MCP server and given messages.
        """
        agent = Agent(
            name="Chatbot Shieldy",
            instructions=system_instructions,
            mcp_servers=[mcp_server],
            # model_settings=ModelSettings(tool_choice="required"),
            model_settings=ModelSettings(tool_choice="auto"),
            model=model
        )
        
        result = await Runner.run(starting_agent=agent, input=messages)
        return str(result.final_output)

    async def _call(self, system_instructions: str, messages: List[dict], model:str) -> str:
        """
        Calls the MCP server with the given user input and returns the response.
        """
        async with MCPServerSse(
                name="SSE Python Server",
                params={
                    "url": "http://localhost:8000/sse",
                },
            ) as server:
                trace_id = gen_trace_id()
                with trace(workflow_name="SQLite call", trace_id=trace_id):
                    # logger.info(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
                    return await self._run(server, system_instructions, messages, model)
                
    def call(self,system_instructions: str,  messages: List[dict], model:str="gpt-4") -> str:
        """
            Wrapper for the async _call function.
        """
        try:
            response = asyncio.run(self._call(system_instructions, messages, model))
            return response
        except Exception as e:
            logger.info(f"Exception on tool call: '{e}'")
            return "Please try again."
                
    def _terminate_process(self):
        """
        Terminates the MCP server process if it is still running.
        """
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
                
if __name__ == "__main__":
    client = MCP_Client()
    messages = []
    while True:
        try:
            user_input = input("Enter your query: ")
            messages.append(UserMessage(user_input))
            n = 10
            messages = messages[-n:]
            response = asyncio.run(client.call(messages))
            logger.info(response)
            messages.append(AssistantMessage(response))
        except Exception as e:
            logger.info(e)
            break