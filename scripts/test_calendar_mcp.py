import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timedelta
from app.mcp.client import get_calendar_tools, unwrap_tool_result


async def main():
    print("Connecting to calendar MCP server...")
    tools = await get_calendar_tools()
    print(f"Available tools: {list(tools.keys())}")

    # Pick a weekday, 2pm — should be within business hours
    test_time = datetime.now() + timedelta(days=2)
    while test_time.weekday() >= 5:  # skip Sat/Sun to land on a real business day
        test_time += timedelta(days=1)
    test_time = test_time.replace(hour=14, minute=0, second=0, microsecond=0)
    iso_time = test_time.isoformat()

    print(f"\nChecking availability for {iso_time} (should be a weekday, within hours)...")
    raw = await tools["check_availability"].ainvoke({"iso_datetime": iso_time})
    result = unwrap_tool_result(raw)
    print(f"Unwrapped result: {result}")

    print(f"\nChecking availability for a Sunday (should be unavailable, outside hours)...")
    sunday = test_time
    while sunday.weekday() != 6:
        sunday += timedelta(days=1)
    raw2 = await tools["check_availability"].ainvoke({"iso_datetime": sunday.isoformat()})
    result2 = unwrap_tool_result(raw2)
    print(f"Unwrapped result: {result2}")

    print(f"\nLooking up a fake booking ID (should be None)...")
    raw3 = await tools["find_appointment_by_booking_id"].ainvoke({"booking_id": "BP000000"})
    result3 = unwrap_tool_result(raw3)
    print(f"Unwrapped result: {result3}")


if __name__ == "__main__":
    asyncio.run(main())