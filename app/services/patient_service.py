from datetime import datetime
from app.db.mongo import get_patients_collection, get_appointments_collection, get_escalations_collection


def upsert_patient(name: str, age, email: str) -> None:
    """Creates or updates the patient record, tracking first/last seen and booking count."""
    patients = get_patients_collection()
    now = datetime.utcnow()

    patients.update_one(
        {"email": email},
        {
            "$set": {"name": name, "age": age, "last_seen": now},
            "$setOnInsert": {"first_seen": now},
            "$inc": {"total_bookings": 1},
        },
        upsert=True,
    )


def log_appointment_created(booking_id: str, event_id: str, patient_name: str,
                              patient_age, patient_email: str, reason: str,
                              scheduled_time: datetime) -> None:
    appointments = get_appointments_collection()
    now = datetime.utcnow()

    appointments.insert_one({
        "booking_id": booking_id,
        "event_id": event_id,
        "patient_name": patient_name,
        "patient_age": patient_age,
        "patient_email": patient_email,
        "reason": reason,
        "status": "booked",
        "scheduled_time": scheduled_time,
        "created_at": now,
        "updated_at": now,
        "history": [{"action": "booked", "time": now, "slot": scheduled_time}],
    })

    upsert_patient(patient_name, patient_age, patient_email)


def log_appointment_rescheduled(booking_id: str, new_slot: datetime) -> None:
    appointments = get_appointments_collection()
    now = datetime.utcnow()

    existing = appointments.find_one({"booking_id": booking_id})
    old_slot = existing["scheduled_time"] if existing else None

    appointments.update_one(
        {"booking_id": booking_id},
        {
            "$set": {"status": "rescheduled", "scheduled_time": new_slot, "updated_at": now},
            "$push": {"history": {"action": "rescheduled", "time": now, "old_slot": old_slot, "new_slot": new_slot}},
        },
    )


def log_appointment_cancelled(booking_id: str) -> None:
    appointments = get_appointments_collection()
    now = datetime.utcnow()

    appointments.update_one(
        {"booking_id": booking_id},
        {
            "$set": {"status": "cancelled", "updated_at": now},
            "$push": {"history": {"action": "cancelled", "time": now}},
        },
    )


def log_escalation(call_sid: str, reason: str, category, message: str) -> None:
    escalations = get_escalations_collection()
    escalations.insert_one({
        "call_sid": call_sid,
        "reason": reason,
        "category": category,
        "message": message,
        "timestamp": datetime.utcnow(),
    })