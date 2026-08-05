# Copyright 2026 Google LLC
# Seed Firestore Database for PWS Care Companion Agent

from google.cloud import firestore

# CRITICAL: Hardcode the string GCP project ID (do NOT use GOOGLE_CLOUD_PROJECT env var or google.auth.default)
PROJECT_ID = "qwiklabs-gcp-04-d2bb10d8ba5b"

db = firestore.Client(project=PROJECT_ID)


def seed_database():
    """Seeds Firestore with initial PWS Care records, appointments, medication logs, and child profile."""
    print(f"Seeding Firestore database for project: {PROJECT_ID}...")

    # 1. Seed Child Profile
    profile_ref = db.collection("pws_child_profile").document("leo_profile")
    profile_ref.set(
        {
            "child_name": "Leo",
            "birthdate": "2023-07-11",
            "pws_stage": "Stage 1b (Early Toddler)",
            "growth_hormone_dose": "0.5 mg daily at bedtime",
            "dietary_calorie_cap": 1200,
            "primary_caregivers": ["John (Father - Admin)", "Sarah (Mother - Admin)"],
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )
    print("✓ Seeded pws_child_profile document 'leo_profile'")

    # 2. Seed Initial Appointments
    appointments = [
        {
            "doc_id": "appt_dr_xyz",
            "doctor": "Dr. XYZ",
            "specialty": "Pediatric Endocrinologist",
            "date": "2026-08-30",
            "time": "09:00 AM",
            "location": "City Children's Hospital",
            "status": "Scheduled",
            "notes": "Annual Growth Hormone therapy review and blood panel check.",
        },
        {
            "doc_id": "appt_dietitian",
            "doctor": "Sarah Jenkins, RD",
            "specialty": "PWS Clinical Dietitian",
            "date": "2026-09-05",
            "time": "02:00 PM",
            "location": "Metabolic Nutrition Clinic",
            "status": "Scheduled",
            "notes": "Review calorie limits and macro balance for early toddler stage.",
        },
    ]

    for appt in appointments:
        doc_id = appt.pop("doc_id")
        appt["created_at"] = firestore.SERVER_TIMESTAMP
        db.collection("pws_appointments").document(doc_id).set(appt)
    print(f"✓ Seeded {len(appointments)} appointments in 'pws_appointments'")

    # 3. Seed Medication Logs
    med_logs = [
        {
            "doc_id": "med_log_101",
            "medication_name": "Growth Hormone Injection",
            "dose": "0.5 mg",
            "date": "2026-08-04",
            "time_administered": "08:00 PM",
            "administered_by": "John (Father)",
            "status": "Completed",
            "notes": "Right thigh injection site. Child was calm.",
        }
    ]

    for med in med_logs:
        doc_id = med.pop("doc_id")
        med["created_at"] = firestore.SERVER_TIMESTAMP
        db.collection("pws_medication_logs").document(doc_id).set(med)
    print(f"✓ Seeded {len(med_logs)} medication logs in 'pws_medication_logs'")

    # 4. Seed Therapy Logs
    therapy_logs = [
        {
            "doc_id": "therapy_log_201",
            "therapy_type": "Physical Therapy (PT)",
            "duration_minutes": 30,
            "date": "2026-08-05",
            "therapist": "Dr. Lee",
            "notes": "Worked on core stability and gross motor balance. Leo held a 30-second plank.",
            "accomplishment": "Core stability milestone achieved",
        }
    ]

    for th in therapy_logs:
        doc_id = th.pop("doc_id")
        th["created_at"] = firestore.SERVER_TIMESTAMP
        db.collection("pws_therapy_logs").document(doc_id).set(th)
    print(f"✓ Seeded {len(therapy_logs)} therapy logs in 'pws_therapy_logs'")

    print("🎉 Firestore database seeding complete!")


if __name__ == "__main__":
    seed_database()
