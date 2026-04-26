import json
import logging
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")

from langchain.schema import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from langgraph_pipeline.state import MovieState
from rag.vector_store import query_movies

logger = logging.getLogger(__name__)

# ─── Mood → semantic theme mapping ───────────────────────────────────────────
MOOD_THEMES = {
    "Happy":       "joyful funny uplifting comedy feel-good cheerful entertaining light",
    "Sad":         "emotional heartbreaking drama melancholy grief comforting healing",
    "Romantic":    "love romance relationship passion couples intimate heartwarming",
    "Excited":     "action adventure thrilling fast-paced adrenaline blockbuster epic",
    "Bored":       "engaging unique creative mind-bending entertaining twist gripping",
    "Fearful":     "horror scary suspense thriller dark mysterious supernatural tense",
    "Adventurous": "adventure exploration journey quest discovery travel epic wilderness",
}

LANG_HINTS = {
    "Hindi":   "Bollywood Hindi Indian cinema Hindustan",
    "Tamil":   "Tamil Kollywood South Indian Tamil Nadu",
    "Telugu":  "Telugu Tollywood South Indian Andhra",
    "English": "Hollywood English American British",
    "Any":     "",
}


# ─── Nodes ───────────────────────────────────────────────────────────────────

def input_node(state: MovieState) -> MovieState:
    logger.info(
        f"[input_node] mood={state['mood']} genre={state['genre']} "
        f"type={state['content_type']} lang={state['language']}"
    )
    return state


def query_builder_node(state: MovieState) -> MovieState:
    mood_text  = MOOD_THEMES.get(state["mood"], state["mood"].lower())
    lang_text  = LANG_HINTS.get(state["language"], state["language"])
    query = (
        f"{mood_text} {state['genre'].lower()} "
        f"{state['content_type'].lower()} {lang_text}"
    )
    logger.info(f"[query_builder_node] query='{query}'")
    return {**state, "query": query}


def retriever_node(state: MovieState) -> MovieState:
    # Retrieve 15 candidates — gives Gemini enough to pick the best 5
    movies = query_movies(state["query"], n_results=15)
    logger.info(f"[retriever_node] retrieved {len(movies)} movies from dataset")
    return {**state, "retrieved_movies": movies}


def gemini_node(state: MovieState) -> MovieState:
    """
    Gemini's ONLY job here:
      • Write an empathetic intro paragraph
      • Select 5 movies BY INDEX from the provided dataset list
      • Write an explanation for each selected movie
      • Write a closing message

    Gemini CANNOT suggest any movie outside the numbered list.
    Movie titles/genres/ratings always come from the dataset (formatter_node).
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        logger.error("GEMINI_API_KEY not configured!")
        return {**state,
                "error": "GEMINI_API_KEY is not set. Please add it to backend/.env",
                "gemini_response": ""}

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.5,
    )

    retrieved = state["retrieved_movies"]

    # Build a numbered dataset list — this is ALL Gemini can choose from
    numbered_list = "\n".join(
        f"{i + 1}. \"{m['title']}\" | Genres: {m['genres']} "
        f"| Rating: {m['vote_average']}/10 "
        f"| Overview: {m['overview'][:180]}"
        for i, m in enumerate(retrieved)
    )

    prompt = f"""You are a STRICT movie recommendation assistant.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES — MUST FOLLOW EXACTLY:
1. You MUST ONLY choose movies from the DATASET LIST provided below.
2. DO NOT suggest, invent, or mention any movie that is NOT in the dataset list.
3. DO NOT use your own training knowledge to add movies.
4. Select movies using their INDEX NUMBER (1 to {len(retrieved)}).
5. If the user's preferred language is "{state['language']}" and none of the
   dataset movies clearly match it, still pick 5 from the list and briefly
   mention the language limitation in your intro.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User Preferences:
  • Mood:         {state['mood']}
  • Genre:        {state['genre']}
  • Content Type: {state['content_type']}
  • Language:     {state['language']}

DATASET LIST — only these movies exist in our system:
{numbered_list}

Your tasks:
1. Write a warm, empathetic 2–3 sentence intro acknowledging the user's mood
   ({state['mood']}) and introducing the recommendations.
   End the intro with a line like:
   "Here are a few {state['language']} {state['genre']} {state['content_type'].lower()}s
    that might [mood-appropriate phrase]:"
2. Select exactly 5 movies from the DATASET LIST above using their index numbers.
3. Write a 2–3 sentence explanation for each selected movie explaining why it
   suits the user's mood ({state['mood']}) and preferences.
4. Write a brief 1–2 sentence warm closing message.

Return ONLY this JSON (no markdown, no code fences, no extra text):
{{
  "intro": "Your empathetic intro here.",
  "selections": [
    {{"index": 2, "explanation": "Why this dataset movie suits the user."}},
    {{"index": 5, "explanation": "Why this dataset movie suits the user."}},
    {{"index": 7, "explanation": "Why this dataset movie suits the user."}},
    {{"index": 9, "explanation": "Why this dataset movie suits the user."}},
    {{"index": 11, "explanation": "Why this dataset movie suits the user."}}
  ],
  "outro": "Warm closing message."
}}

CONSTRAINT: Every "index" value must be an integer between 1 and {len(retrieved)}.
Do not use any index outside this range."""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()
        # Strip markdown code fences if Gemini wraps in them
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw
        raw = raw.strip()
        logger.info("[gemini_node] response received successfully")
        return {**state, "gemini_response": raw}
    except Exception as exc:
        logger.error(f"[gemini_node] error: {exc}")
        return {**state, "error": str(exc), "gemini_response": ""}


def formatter_node(state: MovieState) -> MovieState:
    """
    Builds the final recommendation list.
    Movie data (title, genre, rating) comes 100% from the retrieved dataset.
    Only the explanation text comes from Gemini.
    """
    retrieved = state.get("retrieved_movies", [])

    def _dataset_fallback():
        """Return top-5 dataset movies with their own overview as explanation."""
        recs = [
            {
                "title":       m["title"],
                "genre":       m["genres"],
                "rating":      m["vote_average"],
                "explanation": m["overview"][:350] or "A great match for your preferences.",
            }
            for m in retrieved[:5]
        ]
        intro = (
            f"Here are some {state['genre']} {state['content_type'].lower()}s "
            f"from our database that match your {state['mood'].lower()} mood."
        )
        outro = "Enjoy your watch! Take care. 🍿"
        return recs, intro, outro

    # ── If Gemini didn't return anything, use pure dataset fallback ──
    if not state.get("gemini_response"):
        recs, intro, outro = _dataset_fallback()
        logger.info(f"[formatter_node] fallback: {len(recs)} dataset movies")
        return {**state, "recommendations": recs, "intro": intro, "outro": outro}

    try:
        parsed      = json.loads(state["gemini_response"])
        intro       = parsed.get("intro", "")
        outro       = parsed.get("outro", "")
        selections  = parsed.get("selections", [])

        recommendations = []
        seen_titles = set()

        for sel in selections[:5]:
            try:
                # Convert 1-based Gemini index → 0-based list index
                idx = int(sel.get("index", 0)) - 1
            except (TypeError, ValueError):
                logger.warning(f"[formatter_node] bad index value '{sel.get('index')}' — skip")
                continue

            if not (0 <= idx < len(retrieved)):
                logger.warning(f"[formatter_node] index {idx+1} out of range — skip")
                continue

            movie = retrieved[idx]         # ← title/genre/rating from DATASET
            if movie["title"] in seen_titles:
                continue
            seen_titles.add(movie["title"])

            recommendations.append({
                "title":       movie["title"],          # ← strictly from dataset
                "genre":       movie["genres"],         # ← strictly from dataset
                "rating":      movie["vote_average"],   # ← strictly from dataset
                "explanation": sel.get("explanation", ""),  # ← from Gemini
            })

        # ── Pad to 5 if Gemini returned fewer valid selections ──
        for m in retrieved:
            if len(recommendations) >= 5:
                break
            if m["title"] not in seen_titles:
                recommendations.append({
                    "title":       m["title"],
                    "genre":       m["genres"],
                    "rating":      m["vote_average"],
                    "explanation": m["overview"][:350] or "A great dataset match.",
                })
                seen_titles.add(m["title"])

        logger.info(f"[formatter_node] ✅ {len(recommendations)} movies — all from dataset")
        return {**state,
                "recommendations": recommendations,
                "intro": intro,
                "outro": outro}

    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        logger.warning(f"[formatter_node] parse error ({exc}) — dataset fallback")
        recs, intro, outro = _dataset_fallback()
        return {**state, "recommendations": recs, "intro": intro, "outro": outro}


# ─── Graph assembly ──────────────────────────────────────────────────────────

_graph = None


def build_graph():
    g = StateGraph(MovieState)
    g.add_node("input",        input_node)
    g.add_node("query_builder", query_builder_node)
    g.add_node("retriever",    retriever_node)
    g.add_node("gemini",       gemini_node)
    g.add_node("formatter",    formatter_node)

    g.set_entry_point("input")
    g.add_edge("input",         "query_builder")
    g.add_edge("query_builder", "retriever")
    g.add_edge("retriever",     "gemini")
    g.add_edge("gemini",        "formatter")
    g.add_edge("formatter",     END)

    return g.compile()


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
