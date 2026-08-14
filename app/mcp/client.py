"""
Shared MCP client that connects to all local MCP servers (calendar, email)
over stdio and exposes their tools for LangGraph nodes to call. Servers are
launched as subprocesses automatically when tools are first requested.
"""
import sys
import json
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_EXECUTABLE = sys.executable

_client = MultiServerMCPClient(
    {
        "calendar": {
            "command": PYTHON_EXECUTABLE,
            "args": ["-m", "app.mcp_servers.calendar_server"],
            "transport": "stdio",
            "cwd": str(PROJECT_ROOT),
        },
        "email": {
            "command": PYTHON_EXECUTABLE,
            "args": ["-m", "app.mcp_servers.email_server"],
            "transport": "stdio",
            "cwd": str(PROJECT_ROOT),
        },
    }
)


async def get_calendar_tools():
    """Returns the calendar server's tools as LangChain-compatible tool objects, keyed by name."""
    tools = await _client.get_tools(server_name="calendar")
    return {tool.name: tool for tool in tools}


async def get_email_tools():
    """Returns the email server's tools as LangChain-compatible tool objects, keyed by name."""
    tools = await _client.get_tools(server_name="email")
    return {tool.name: tool for tool in tools}


def unwrap_tool_result(raw_result):
    """
    MCP tool results come back as a list of content blocks, e.g.
    [{"type": "text", "text": "{...json...}", "id": "..."}] or [] for null/empty.
    Unwraps this into a plain Python value for normal use in graph nodes.
    """
    if not raw_result:
        return None
    first = raw_result[0]
    text = first.get("text") if isinstance(first, dict) else getattr(first, "text", None)
    if text is None:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text