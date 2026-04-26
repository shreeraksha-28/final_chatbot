import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from langgraph_pipeline.graph import get_graph
from services.chat_service import get_session_preferences

logger = logging.getLogger(__name__)
router = APIRouter()


class RecommendRequest(BaseModel):
    session_id: Optional[str] = None
    mood: Optional[str] = None
    genre: Optional[str] = None
    content_type: Optional[str] = None
    language: Optional[str] = None


@router.post("/recommend")
async def recommend(body: RecommendRequest):
    """
    Run the LangGraph pipeline and return:
      - intro:           empathetic opening from Gemini
      - recommendations: 5 movies strictly from the TMDB dataset
      - outro:           warm closing from Gemini
    """
    # Resolve preferences from session or direct body
    if body.session_id:
        prefs = get_session_preferences(body.session_id)
        if not prefs:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        prefs = {
            "mood":         body.mood,
            "genre":        body.genre,
            "content_type": body.content_type,
            "language":     body.language,
        }

    missing = [k for k, v in prefs.items() if not v]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing preferences: {', '.join(missing)}",
        )

    try:
        graph = get_graph()
        initial_state = {
            "mood":            prefs["mood"],
            "genre":           prefs["genre"],
            "content_type":    prefs["content_type"],
            "language":        prefs["language"],
            "query":           "",
            "retrieved_movies": [],
            "gemini_response": "",
            "recommendations": [],
            "intro":           "",
            "outro":           "",
            "error":           None,
        }
        result = graph.invoke(initial_state)

        if result.get("error") and not result.get("recommendations"):
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "session_id":      body.session_id,
            "preferences":     prefs,
            "intro":           result.get("intro", ""),
            "recommendations": result["recommendations"],
            "outro":           result.get("outro", ""),
            "total":           len(result["recommendations"]),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Recommendation pipeline error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
