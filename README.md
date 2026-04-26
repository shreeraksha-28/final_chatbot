# 🎬 CineAI — AI-Powered Movie Recommender Chatbot

A full-stack conversational movie recommendation system using:
- **React + Vite** frontend with dark glassmorphism UI
- **FastAPI** backend with LangChain/LangGraph pipeline
- **HuggingFace** embeddings (all-MiniLM-L6-v2, runs locally)
- **ChromaDB** vector store (persisted to disk)
- **Gemini 1.5 Flash** for personalized recommendation generation
- **TMDB dataset** (~4,800 movies)

---

## 📁 Project Structure

```
chatbot/
├── backend/          # FastAPI + RAG + LangGraph
├── frontend/         # React + Vite UI
├── chroma_db/        # Auto-generated on first run
├── tmdb_merged.csv   # Your dataset
└── README.md
```

---

## ⚡ Quick Start

### 1. Add your Gemini API Key

Edit `backend/.env`:
```
GEMINI_API_KEY=your_actual_key_here
```
Get a free key at: https://aistudio.google.com/app/apikey

---

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> ⏳ **First run**: Building the ChromaDB index takes ~2-5 minutes.  
> Subsequent starts are instant (index is cached to `chroma_db/`).

---

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open: **http://localhost:5173**

---

## 🧠 How It Works

```
User selects Mood → Genre → Content Type → Language
        ↓
  LangGraph Pipeline:
  1. input_node       — validate preferences
  2. query_builder    — build semantic query from mood + genre
  3. retriever_node   — ChromaDB similarity search (top 10)
  4. gemini_node      — Gemini 1.5 Flash generates 5 personalized recs
  5. formatter_node   — parse & structure JSON response
        ↓
   React UI displays recommendation cards
```

---

## 🌐 API Reference

| Method | Endpoint      | Description                        |
|--------|---------------|------------------------------------|
| POST   | /chat/start   | Start new chat session             |
| POST   | /chat/step    | Submit step answer, get next step  |
| POST   | /recommend    | Get 5 recommendations              |
| GET    | /health       | Health check                       |

API docs: http://localhost:8000/docs

---

## 🔧 Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Frontend    | React 18, Vite 5, Vanilla CSS       |
| Backend     | FastAPI, Uvicorn                    |
| Embeddings  | sentence-transformers/all-MiniLM-L6-v2 |
| Vector DB   | ChromaDB (persistent)               |
| Orchestration | LangChain + LangGraph             |
| LLM         | Google Gemini 1.5 Flash             |
| Dataset     | TMDB (~4,800 movies)                |
