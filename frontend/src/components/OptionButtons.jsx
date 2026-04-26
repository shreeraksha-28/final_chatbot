export default function OptionButtons({ options, onSelect, disabled, selected }) {
  return (
    <div className="options-row">
      {options.map((opt) => (
        <button
          key={opt}
          id={`option-${opt.replace(/\s+/g, '-').toLowerCase()}`}
          className={`option-chip ${selected === opt ? 'selected' : ''}`}
          onClick={() => onSelect(opt)}
          disabled={disabled}
        >
          {opt}
        </button>
      ))}
    </div>
  )
}
