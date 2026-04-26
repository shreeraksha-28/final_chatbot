const RANK_EMOJIS = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']

export default function RecommendationCard({ rec, index }) {
  const rank   = RANK_EMOJIS[index] ?? `${index + 1}.`
  const rating = typeof rec.rating === 'number'
    ? rec.rating.toFixed(1)
    : rec.rating

  // Show primary genre only (first item before comma)
  const primaryGenre = rec.genre
    ? rec.genre.split(',')[0].trim()
    : ''

  return (
    <div
      className="rec-card"
      id={`rec-card-${index + 1}`}
      style={{ animationDelay: `${index * 0.09}s` }}
    >
      {/* ── Rank + Number ── */}
      <div className="rec-card-header">
        <span className="rec-rank">{rank}</span>
        <div style={{ flex: 1 }}>

          {/* Title */}
          <div className="rec-label">Title:</div>
          <div className="rec-title">{rec.title}</div>

          {/* Genre + Rating badges */}
          <div className="rec-meta">
            {primaryGenre && (
              <span className="rec-badge genre">{primaryGenre}</span>
            )}
            {rating && (
              <span className="rec-badge rating">⭐ {rating}/10</span>
            )}
          </div>
        </div>
      </div>

      {/* Genre label row */}
      {rec.genre && (
        <div className="rec-field-row">
          <span className="rec-field-label">Genre:</span>
          <span className="rec-field-value">{rec.genre}</span>
        </div>
      )}

      {/* Explanation */}
      {rec.explanation && (
        <div className="rec-field-row">
          <span className="rec-field-label">Explanation:</span>
          <span className="rec-explanation-text">{rec.explanation}</span>
        </div>
      )}
    </div>
  )
}
