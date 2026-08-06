# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore
from google.genai import types

MODEL = "gemini-2.5-flash"

# CRITICAL: Hardcode project ID as string for Firestore client (never read from env or google.auth.default)
PROJECT_ID = "qwiklabs-gcp-04-d2bb10d8ba5b"
db = firestore.Client(project=PROJECT_ID)

# Vertex AI RAG Corpus ID for PWS Medical Guidelines
RAG_CORPUS_NAME = "projects/872367567135/locations/us-central1/ragCorpora/162349488910893056"


# WRITE: after each turn, send the session to Vertex AI Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    """Callback triggered after each turn to extract and store durable facts into Memory Bank."""
    await callback_context.add_session_to_memory()
    return None


# --- RAG RETRIEVAL TOOL ---

def consult_pws_medical_guidelines(query: str) -> str:
    """Searches official Prader-Willi Syndrome (PWS) medical guidelines and caregiver publications.

    Covers clinical guidelines for anesthesia precautions, Growth Hormone protocols, GI & gastroparesis
    algorithms, central adrenal insufficiency, 7 nutritional phases, food security, and dental care.
    Call this whenever answering clinical, dietary, or medical care questions about PWS.

    Args:
        query: Medical topic or clinical question to look up (e.g. 'anesthesia precautions', 'growth hormone guidelines', 'gastroparesis', 'nutritional phases', 'constipation', 'dental care').
    """
    import vertexai
    from vertexai import rag

    vertexai.init(project=PROJECT_ID, location="us-central1")
    try:
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
    except Exception as e:
        return f"Retrieval error: {e}"

    contexts = getattr(resp.contexts, "contexts", [])
    passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
    return "\n\n---\n\n".join(passages) or "No specific medical passage found for that query in the guidelines."


# --- FIRESTORE READ TOOLS ---

def get_upcoming_appointments() -> str:
    """Retrieves upcoming medical and specialist appointments from Firestore database."""
    docs = db.collection("pws_appointments").stream()
    appts = [doc.to_dict() for doc in docs]
    if not appts:
        return "No upcoming appointments found in database."
    res = []
    for a in appts:
        res.append(
            f"- {a.get('doctor')} ({a.get('specialty')}): {a.get('date')} at {a.get('time')} - {a.get('location')}. "
            f"Status: {a.get('status')}. Notes: {a.get('notes', '')}"
        )
    return "Upcoming Appointments:\n" + "\n".join(res)


def get_child_profile() -> str:
    """Retrieves care profile and preferences for the child (birthdate, PWS stage, dietary caps) from Firestore."""
    doc = db.collection("pws_child_profile").document("leo_profile").get()
    if not doc.exists:
        return "No profile found for child."
    data = doc.to_dict()
    return (
        f"Child Care Profile: {data.get('child_name')}\n"
        f"- Birthdate: {data.get('birthdate')} (Born July 11, 2023)\n"
        f"- PWS Stage: {data.get('pws_stage')}\n"
        f"- Growth Hormone Protocol: {data.get('growth_hormone_dose')}\n"
        f"- Daily Calorie Cap: {data.get('dietary_calorie_cap')} kcal\n"
        f"- Primary Caregivers: {', '.join(data.get('primary_caregivers', []))}"
    )


def get_medication_logs(days: int = 30) -> str:
    """Retrieves medication and Growth Hormone injection logs from Firestore for the specified timeframe (default: last 30 days)."""
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    docs = db.collection("pws_medication_logs").stream()
    all_logs = [doc.to_dict() for doc in docs]
    logs = [l for l in all_logs if l.get('date', '') >= cutoff or not l.get('date')]
    if not logs:
        return f"No medication logs found in the last {days} days. (Total historical database records: {len(all_logs)})."
    res = [
        f"- {l.get('medication_name')} ({l.get('dose')}): Administered on {l.get('date')} at {l.get('time_administered')} by {l.get('administered_by')}."
        for l in logs
    ]
    return f"Medication Logs (Last {days} Days Window - {len(logs)} of {len(all_logs)} DB entries):\n" + "\n".join(res)


def get_therapy_logs(days: int = 30) -> str:
    """Retrieves therapy progress and session logs (Physical, Occupational, Speech, Behavioral) from Firestore for the specified timeframe (default: last 30 days)."""
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    docs = db.collection("pws_therapy_logs").stream()
    all_logs = [doc.to_dict() for doc in docs]
    logs = [l for l in all_logs if l.get('date', '') >= cutoff or not l.get('date')]
    if not logs:
        return f"No therapy logs found in the last {days} days. (Total historical database records: {len(all_logs)})."
    res = [
        f"- {l.get('therapy_type')} ({l.get('duration_minutes')} mins) on {l.get('date')}: {l.get('notes')} Accomplishment: {l.get('accomplishment', '')}"
        for l in logs
    ]
    return f"Therapy Logs (Last {days} Days Window - {len(logs)} of {len(all_logs)} DB entries):\n" + "\n".join(res)


# --- FIRESTORE WRITE TOOLS ---

def add_appointment(doctor: str, specialty: str, date: str, time: str, location: str, notes: str = "") -> str:
    """Adds a new medical or specialist appointment to the Firestore database.

    Args:
        doctor: Name of doctor or specialist (e.g. 'Dr. XYZ').
        specialty: Specialty field (e.g. 'Pediatric Endocrinologist').
        date: Date string (e.g. '2026-08-30').
        time: Time string (e.g. '09:00 AM').
        location: Hospital or clinic name (e.g. 'City Children's Hospital').
        notes: Additional notes or prep details.
    """
    doc_ref = db.collection("pws_appointments").document()
    data = {
        "doctor": doctor,
        "specialty": specialty,
        "date": date,
        "time": time,
        "location": location,
        "status": "Scheduled",
        "notes": notes,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    doc_ref.set(data)
    return f"Appointment with {doctor} on {date} at {time} saved successfully to Firestore."


def log_medication_dose(medication_name: str, dose: str, time_administered: str, administered_by: str, notes: str = "") -> str:
    """Logs a medication or Growth Hormone injection dose into Firestore database.

    Args:
        medication_name: Name of medication (e.g. 'Growth Hormone Injection').
        dose: Dosage amount (e.g. '0.5 mg').
        time_administered: Time administered (e.g. '08:00 PM').
        administered_by: Name of caregiver who gave dose (e.g. 'John (Father)').
        notes: Optional observation notes.
    """
    doc_ref = db.collection("pws_medication_logs").document()
    data = {
        "medication_name": medication_name,
        "dose": dose,
        "date": datetime.date.today().isoformat(),
        "time_administered": time_administered,
        "administered_by": administered_by,
        "status": "Completed",
        "notes": notes,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    doc_ref.set(data)
    return f"Logged medication dose ({medication_name} - {dose}) to Firestore."


def log_therapy_session(therapy_type: str, duration_minutes: int, notes: str, accomplishment: str = "") -> str:
    """Logs progress from a therapy session into Firestore database.

    Args:
        therapy_type: Therapy category ('Physical Therapy', 'Occupational Therapy', 'Speech Therapy', 'Behavioral Therapy').
        duration_minutes: Duration of session in minutes.
        notes: Progress and session notes.
        accomplishment: Milestone or goal achieved.
    """
    doc_ref = db.collection("pws_therapy_logs").document()
    data = {
        "therapy_type": therapy_type,
        "duration_minutes": duration_minutes,
        "date": datetime.date.today().isoformat(),
        "notes": notes,
        "accomplishment": accomplishment,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    doc_ref.set(data)
    return f"Logged {therapy_type} session ({duration_minutes} mins) to Firestore."


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are PWS Care Companion, an expert and deeply empathetic AI care assistant for caregivers "
        "and family members of children with Prader-Willi Syndrome (PWS).\n\n"
        "CRITICAL GROUNDING MANDATE:\n"
        "You are grounded on official PWS medical guidelines and clinical publications (from FPWR and PWSA USA) "
        "stored in your Vertex AI RAG Corpus. Whenever answering ANY question regarding medical care, anesthesia "
        "precautions, Growth Hormone protocols, GI/gastroparesis algorithms, 7 nutritional phases, food security, "
        "or dental health for PWS, you MUST call your `consult_pws_medical_guidelines` tool first to retrieve "
        "passages from these documents and ground your answer on the retrieved facts.\n\n"
        "CARE RECORD MANAGEMENT:\n"
        "Use your Firestore database tools (`get_upcoming_appointments`, `add_appointment`, `get_child_profile`, "
        "`get_medication_logs`, `log_medication_dose`, `get_therapy_logs`, `log_therapy_session`) to read and persist "
        "all care records reliably."
    ),
    tools=[
        PreloadMemoryTool(),
        consult_pws_medical_guidelines,
        get_upcoming_appointments,
        get_child_profile,
        get_medication_logs,
        get_therapy_logs,
        add_appointment,
        log_medication_dose,
        log_therapy_session,
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
