import { formatPrice } from '../money'

export default function Confirmation({ t, order, onDone }) {
  return (
    <div className="app confirm">
      <img className="confirm-logo" src="/logo.svg" alt="" />
      <h2>{t.orderPlaced}</h2>
      <p className="order-no">{t.orderNumber} #{order.orderId}</p>
      <p className="muted">{t.total} {formatPrice(order.total)}</p>
      {order.points != null && <p className="points">⭐ {t.pointsNow(order.points)}</p>}
      <button className="primary" onClick={onDone}>{t.orderMore}</button>
    </div>
  )
}
