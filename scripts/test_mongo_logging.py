import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.mongo import get_patients_collection, get_appointments_collection, get_escalations_collection

if __name__ == "__main__":
    patients = get_patients_collection()
    appointments = get_appointments_collection()
    escalations = get_escalations_collection()

    print(f"patients: {patients.count_documents({})} documents")
    for p in patients.find().limit(5):
        print(f"  {p['name']} — {p['email']} — bookings: {p.get('total_bookings')}")

    print(f"\nappointments: {appointments.count_documents({})} documents")
    for a in appointments.find().sort("created_at", -1).limit(5):
        print(f"  {a['booking_id']} — {a['patient_name']} — {a['status']} — {a['scheduled_time']}")

    print(f"\nescalations: {escalations.count_documents({})} documents")
    for e in escalations.find().sort("timestamp", -1).limit(5):
        print(f"  {e['reason']} — {e.get('category')} — {e['message'][:50]}")