import { useState } from 'react'
import ChatWindow from '../components/ChatWindow'

export default function Home() {
  const [key, setKey] = useState(0)

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <span className="header-logo">🎬</span>
        <div>
          <div className="header-title">CineAI</div>
          <div className="header-subtitle">Mood-based movie recommendations</div>
        </div>
        <span className="header-badge">RAG + Gemini</span>
      </header>

      {/* Chat — remount on reset by changing key */}
      <ChatWindow key={key} onReset={() => setKey(k => k + 1)} />
    </div>
  )
}
