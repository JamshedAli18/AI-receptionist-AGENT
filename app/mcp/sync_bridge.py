"""
LangGraph nodes in this project are synchronous functions, but MCP tool
calls are async. This bridges the two by running the async MCP client
calls inside a dedicated event loop, so node functions can call MCP tools
with a plain synchronous function call.
"""
import asyncio
import threading

_loop = None
_loop_thread = None


def _start_background_loop():
    global _loop, _loop_thread
    if _loop is not None:
        return
    _loop = asyncio.new_event_loop()
    _loop_thread = threading.Thread(target=_loop.run_forever, daemon=True)
    _loop_thread.start()


def run_async(coro):
    """Runs an async coroutine from synchronous code and returns its result."""
    _start_background_loop()
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result()