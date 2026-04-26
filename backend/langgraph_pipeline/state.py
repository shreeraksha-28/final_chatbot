from typing import List, Optional, TypedDict


class MovieState(TypedDict):
    mood: str
    genre: str
    content_type: str
    language: str
    query: str
    retrieved_movies: List[dict]
    gemini_response: str
    recommendations: List[dict]
    intro: str          # warm opening paragraph from Gemini
    outro: str          # closing message from Gemini
    error: Optional[str]
