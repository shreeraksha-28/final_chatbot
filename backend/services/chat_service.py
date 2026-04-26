import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Conversation steps definition ───────────────────────────────────────────
STEPS = [
    {
        "step": 1,
        "key": "mood",
        "question": "How are you feeling today? 😊",
        "options": ["Happy", "Sad", "Romantic", "Excited", "Bored", "Fearful", "Adventurous"],
    },
    {
        "step": 2,
        "key": "genre",
        "question": "What genre do you prefer? 🎬",
        "options": ["Action", "Comedy", "Drama", "Romance", "Thriller", "Horror", "Sci-Fi"],
    },
    {
        "step": 3,
        "key": "content_type",
        "question": "Do you want a Movie or a TV Show? 📺",
        "options": ["Movie", "TV Show"],
    },
    {
        "step": 4,
        "key": "language",
        "question": "What's your preferred language? 🌍",
        "options": ["English", "Hindi", "Tamil", "Telugu", "Any"],
    },
]

# In-memory session store  {session_id: {...}}
_sessions: dict = {}


def create_session() -> dict:
    sid = str(uuid.uuid4())
    _sessions[sid] = {
        "step": 1,
        "mood": None,
        "genre": None,
        "content_type": None,
        "language": None,
        "complete": False,
    }
    logger.info(f"Created session {sid}")
    first = STEPS[0]
    return {
        "session_id": sid,
        "step": 1,
        "question": first["question"],
        "options": first["options"],
        "message": (
            "🎬 Welcome! I'm your personal AI movie guide. "
            "Answer a few quick questions and I'll find the perfect watch for you!"
        ),
        "ready_to_recommend": False,
    }


def process_step(session_id: str, step: int, answer: str) -> dict:
    if session_id not in _sessions:
        raise ValueError(f"Session '{session_id}' not found. Please start a new chat.")

    session = _sessions[session_id]
    step_def = STEPS[step - 1]

    # Store the answer
    session[step_def["key"]] = answer
    session["step"] = step + 1

    # More steps remaining
    if step < len(STEPS):
        next_def = STEPS[step]
        return {
            "session_id": session_id,
            "step": step + 1,
            "question": next_def["question"],
            "options": next_def["options"],
            "completed_steps": step,
            "ready_to_recommend": False,
        }

    # All steps done
    session["complete"] = True
    return {
        "session_id": session_id,
        "step": 5,
        "question": None,
        "options": [],
        "completed_steps": 4,
        "ready_to_recommend": True,
        "preferences": {
            "mood": session["mood"],
            "genre": session["genre"],
            "content_type": session["content_type"],
            "language": session["language"],
        },
    }


def get_session_preferences(session_id: str) -> Optional[dict]:
    s = _sessions.get(session_id)
    if not s:
        return None
    return {
        "mood": s.get("mood"),
        "genre": s.get("genre"),
        "content_type": s.get("content_type"),
        "language": s.get("language"),
    }
