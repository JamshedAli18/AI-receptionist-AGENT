# scripts/test_calendar.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timedelta
from app.services.calendar_service import check_availability

test_time = datetime.now() + timedelta(days=1)
test_time = test_time.replace(hour=14, minute=0, second=0, microsecond=0)

available = check_availability(test_time)
print(f"Slot at {test_time} available: {available}")