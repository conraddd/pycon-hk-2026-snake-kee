import { useState } from 'react'
import { formatPrice, imageFor, linePrice } from '../money'

function describe(line, t) {
  return [
    line.temperature && t[line.temperature],
    line.sweetness && t.sweetnessOptions[line.sweetness],
    line.ice && t.iceOptions[line.ice],
  ].filter(Boolean).join(' · ')
}

export default function CartSheet({ t, lang, cart, total, onRemove, onPlace, onClose }) {
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setFailed(false)
    try {
      await onPlace(email.trim())
    } catch {
      setFailed(true)
      setBusy(false)
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <form className="sheet" onClick={(e) => e.stopPropagation()} onSubmit={submit} aria-label={t.yourOrder}>
        <button type="button" className="close" onClick={onClose} aria-label={t.close}>×</button>
        <h3>{t.yourOrder}</h3>
        {cart.length === 0 && <p className="muted">{t.empty}</p>}
        <ul className="lines">
          {cart.map((line) => (
            <li key={line.key}>
              <img src={imageFor(line.item, line.temperature)} alt="" />
              <div className="line-text">
                <div>{line.qty} × {line.item.name[lang]}</div>
                <div className="muted small">{describe(line, t)}</div>
              </div>
              <div className="line-price">{formatPrice(linePrice(line) * line.qty)}</div>
              <button type="button" className="remove" onClick={() => onRemove(line.key)} aria-label={t.remove}>×</button>
            </li>
          ))}
        </ul>

        <label className="rewards">
          <span className="rewards-title">🐍 {t.rewardsTitle}</span>
          <span className="muted small">{t.rewardsBody}</span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                 placeholder={t.emailPlaceholder} autoComplete="email" />
        </label>

        {failed && <p className="error">{t.error}</p>}
        <div className="sheet-foot">
          <div className="total">
            <span className="muted small">{t.total}</span>
            <strong>{formatPrice(total)}</strong>
          </div>
          <button className="primary" disabled={busy || cart.length === 0}>{busy ? t.placing : t.placeOrder}</button>
        </div>
      </form>
    </div>
  )
}
