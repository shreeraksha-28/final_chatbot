export default function Message({ role, text }) {
  const isBot = role === 'bot'
  return (
    <div className={`message-row ${isBot ? 'bot' : 'user'}`}>
      <div className={`avatar ${isBot ? 'bot' : 'user'}`}>
        {isBot ? '🤖' : '🧑'}
      </div>
      <div className={`bubble ${isBot ? 'bot' : 'user'}`}>
        {text}
      </div>
    </div>
  )
}
