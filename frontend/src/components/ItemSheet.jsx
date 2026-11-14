import { useState } from 'react'
import { formatPrice, imageFor, linePrice } from '../money'

function Choice({ label, options, value, onChange }) {
  return (
    <fieldset className="choice">
      <legend>{label}</legend>
      <div className="pills">
        {options.map(([v, text]) => (
          <button key={v} type="button" className={v === value ? 'pill on' : 'pill'} onClick={() => onChange(v)}>
            {text}
          </button>
        ))}
      </div>
    </fieldset>
  )
}

export default function ItemSheet({ item, lang, t, options, onAdd, onClose }) {
  const isDrink = item.category === 'drink'
  const canBeIced = item.icedSurcharge != null && !item.icedOnly
  const [temperature, setTemperature] = useState(item.icedOnly ? 'iced' : 'hot')
  const [sweetness, setSweetness] = useState(options.sweetness[0])
  const [ice, setIce] = useState(options.ice[0])
  const [qty, setQty] = useState(1)

  const line = { item, qty, temperature: isDrink ? temperature : '', sweetness: isDrink ? sweetness : '',
                 ice: isDrink && temperature === 'iced' ? ice : '' }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()} role="dialog" aria-label={item.name[lang]}>
        <button className="close" onClick={onClose} aria-label={t.close}>×</button>
        <img className="sheet-img" src={imageFor(item, temperature)} alt="" />
        <h3>{item.name[lang]}</h3>
        <p className="muted">{item.description[lang]}</p>

        {isDrink && canBeIced && (
          <Choice label={t.temperature} value={temperature} onChange={setTemperature}
                  options={[['hot', t.hot], ['iced', `${t.iced} +${formatPrice(item.icedSurcharge)}`]]} />
        )}
        {isDrink && (
          <Choice label={t.sweetness} value={sweetness} onChange={setSweetness}
                  options={options.sweetness.map((s) => [s, t.sweetnessOptions[s]])} />
        )}
        {isDrink && temperature === 'iced' && (
          <Choice label={t.ice} value={ice} onChange={setIce}
                  options={options.ice.map((s) => [s, t.iceOptions[s]])} />
        )}

        <div className="sheet-foot">
          <div className="stepper" aria-label={t.quantity}>
            <button onClick={() => setQty(Math.max(1, qty - 1))} aria-label="−">−</button>
            <span>{qty}</span>
            <button onClick={() => setQty(qty + 1)} aria-label="+">+</button>
          </div>
          <button className="primary" onClick={() => onAdd(line)}>
            {t.addToOrder} · {formatPrice(linePrice(line) * qty)}
          </button>
        </div>
      </div>
    </div>
  )
}
