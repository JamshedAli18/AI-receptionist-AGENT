import sys
import httpx
sys.path.insert(0, ".")

BASE = "http://localhost:8000"

if __name__ == "__main__":
    password = input("Enter admin password to test: ")

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        # Login
        resp = client.post("/admin/api/login", json={"password": password})
        print(f"Login: {resp.status_code} — {resp.json()}")

        if resp.status_code != 200:
            sys.exit(1)

        # Cookie is automatically stored in the client's cookie jar
        stats = client.get("/admin/api/stats")
        print(f"\nStats: {stats.json()}")

        appointments = client.get("/admin/api/appointments")
        print(f"\nAppointments ({len(appointments.json())}):")
        for a in appointments.json()[:3]:
            print(f"  {a.get('booking_id')} — {a.get('patient_name')} — {a.get('status')}")

        escalations = client.get("/admin/api/escalations")
        print(f"\nEscalations ({len(escalations.json())}):")
        for e in escalations.json()[:3]:
            print(f"  {e.get('reason')} — {e.get('category')} — {e.get('message', '')[:40]}")