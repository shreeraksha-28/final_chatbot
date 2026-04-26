import { useEffect, useRef, useState } from 'react'
import { startChat, sendStep, getRecommendations } from '../api/chatApi'
import LoadingDots from './LoadingDots'
import Message from './Message'
import OptionButtons from './OptionButtons'
import RecommendationCard from './RecommendationCard'

export default function ChatWindow({ onReset }) {
  const [messages, setMessages]           = useState([])
  const [currentOptions, setCurrentOptions] = useState([])
  const [currentStep, setCurrentStep]     = useState(null)
  const [sessionId, setSessionId]         = useState(null)
  const [loading, setLoading]             = useState(false)
  const [recommendations, setRecommendations] = useState([])
  const [done, setDone]                   = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState(null)
  const [error, setError]                 = useState(null)
  const bottomRef = useRef(null)

  // Auto-scroll on every update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading, recommendations])

  // Boot the chat on mount
  useEffect(() => { initChat() }, [])

  async function initChat() {
    setLoading(true)
    try {
      const data = await startChat()
      setSessionId(data.session_id)
      setCurrentStep(data.step)
      setMessages([
        { role: 'bot', text: data.message },
        { role: 'bot', text: data.question },
      ])
      setCurrentOptions(data.options)
    } catch {
      setError('⚠️ Cannot connect to the backend. Make sure FastAPI is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  async function handleOptionSelect(answer) {
    if (loading || done) return
    setSelectedAnswer(answer)
    setMessages(prev => [...prev, { role: 'user', text: answer }])
    setCurrentOptions([])
    setLoading(true)

    try {
      const stepData = await sendStep(sessionId, currentStep, answer)

      if (stepData.ready_to_recommend) {
        setMessages(prev => [
          ...prev,
          { role: 'bot', text: '🔍 Searching our movie database for the perfect picks...' },
        ])

        const recData = await getRecommendations(sessionId)

        // Show Gemini's empathetic intro as a bot message
        if (recData.intro) {
          setMessages(prev => [...prev, { role: 'bot', text: recData.intro }])
        }

        setRecommendations(recData.recommendations || [])

        // Show Gemini's closing message as a bot message
        if (recData.outro) {
          // We'll add outro after cards render — store it
          setMessages(prev => [...prev, { role: 'bot', text: '__CARDS__' }])
          setTimeout(() => {
            setMessages(prev => [
              ...prev.filter(m => m.text !== '__CARDS__'),
              { role: 'bot', text: recData.outro },
            ])
          }, (recData.recommendations?.length || 0) * 90 + 400)
        }

        setDone(true)
      } else {
        setMessages(prev => [...prev, { role: 'bot', text: stepData.question }])
        setCurrentStep(stepData.step)
        setCurrentOptions(stepData.options)
        setSelectedAnswer(null)
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Something went wrong.'
      setMessages(prev => [...prev, { role: 'bot', text: `❌ ${msg}` }])
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const TOTAL_STEPS  = 4
  const completedSteps = done ? 4 : Math.max(0, (currentStep || 1) - 1)

  return (
    <>
      {/* ── Step progress dots ── */}
      <div className="progress-bar" role="progressbar" aria-label="Chat progress">
        {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
          <div
            key={i}
            className={`progress-dot ${
              i < completedSteps ? 'done'
              : i === completedSteps && !done ? 'active'
              : ''
            }`}
          />
        ))}
      </div>

      {/* ── Chat area ── */}
      <div className="chat-window" id="chat-window">

        {/* Messages (skip the __CARDS__ placeholder) */}
        {messages
          .filter(m => m.text !== '__CARDS__')
          .map((m, i) => <Message key={i} role={m.role} text={m.text} />)}

        {loading && <LoadingDots />}

        {/* Option chips */}
        {!loading && currentOptions.length > 0 && !done && (
          <OptionButtons
            options={currentOptions}
            onSelect={handleOptionSelect}
            disabled={loading}
            selected={selectedAnswer}
          />
        )}

        {/* Recommendation cards — inserted BEFORE the outro message */}
        {recommendations.length > 0 && (
          <div className="recs-section">
            <div className="recs-title">🍿 Your Personalized Recommendations</div>
            {recommendations.map((rec, i) => (
              <RecommendationCard key={i} rec={rec} index={i} />
            ))}
          </div>
        )}

        {/* Restart button (shown after outro message) */}
        {done && !loading && (
          <div style={{ textAlign: 'center', marginTop: '8px' }}>
            <button className="restart-btn" id="restart-btn" onClick={onReset}>
              🔄 Start Over
            </button>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </>
  )
}
