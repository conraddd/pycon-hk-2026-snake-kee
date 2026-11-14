import { formatPrice } from '../money'

export default function MenuItemCard({ item, lang, t, onSelect }) {
  const other = lang === 'en' ? 'zh' : 'en'
  return (
    <button className="card" onClick={onSelect}>
      <img src={item.image} alt="" loading="lazy" />
      <div className="card-body">
        <div className="card-name">{item.name[lang]}</div>
        <div className="card-sub">{item.name[other]}</div>
        <div className="card-desc">{item.description[lang]}</div>
        <div className="card-foot">
          <span className="price">{formatPrice(item.price)}</span>
          <span className="add" aria-label={t.add}>+</span>
        </div>
      </div>
    </button>
  )
}
