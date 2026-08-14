import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timedelta
from app.config import TEST_PATIENT_EMAILS
from app.mcp.client import get_email_tools, unwrap_tool_result


async def main():
    if not TEST_PATIENT_EMAILS:
        print("❌ No TEST_PATIENT_EMAIL_1/2 set in .env — cannot test.")
        return

    test_email = TEST_PATIENT_EMAILS[0]
    print("Connecting to email MCP server...")
    tools = await get_email_tools()
    print(f"Available tools: {list(tools.keys())}")

    test_time = (datetime.now() + timedelta(days=2)).isoformat()

    print(f"\nSending clinic notification (Resend)...")
    raw = await tools["notify_clinic_new_booking"].ainvoke({
        "booking_id": "BP888888",
        "patient_name": "MCP Test Patient",
        "patient_age": 30,
        "patient_email": test_email,
        "reason": "MCP email server test",
        "iso_scheduled_time": test_time,
    })
    print(f"Result: {unwrap_tool_result(raw)}")

    print(f"\nSending patient confirmation to whitelisted address {test_email} (Gmail SMTP)...")
    raw2 = await tools["send_patient_booking_confirmation"].ainvoke({
        "patient_email": test_email,
        "patient_name": "MCP Test Patient",
        "booking_id": "BP888888",
        "iso_scheduled_time": test_time,
        "reason": "MCP email server test",
    })
    print(f"Result: {unwrap_tool_result(raw2)}")


if __name__ == "__main__":
    asyncio.run(main())