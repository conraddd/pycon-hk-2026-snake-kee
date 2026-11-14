import { useEffect, useMemo, useRef, useState } from 'react'
import { STRINGS } from './i18n'
import MenuItemCard from './components/MenuItemCard'
import ItemSheet from './components/ItemSheet'
import CartSheet from './components/CartSheet'
import Confirmation from './components/Confirmation'
import { formatPrice, linePrice } from './money'

// The QR code on each table encodes the shop and table, e.g. /?shop=1&table=12
const params = new URLSearchParams(window.location.search)
const SHOP_ID = Number.parseInt(params.get('shop'), 10) || 1
const TABLE_NO = Number.parseInt(params.get('table'), 10) || null
let nextLineKey = 1 // unique key per cart line

export default function App() {
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'en')
  const [menu, setMenu] = useState(null)
  const [error, setError] = useState(null)
  const [activeCategory, setActiveCategory] = useState('drink')
  const [selected, setSelected] = useState(null) // item being customised
  const [cart, setCart] = useState([])
  const [cartOpen, setCartOpen] = useState(false)
  const [placed, setPlaced] = useState(null)
  const sectionRefs = useRef({})
  const t = STRINGS[lang]

  useEffect(() => {
    localStorage.setItem('lang', lang)
    document.documentElement.lang = lang === 'zh' ? 'zh-Hant-HK' : 'en'
  }, [lang])

  useEffect(() => {
    fetch(`/api/menu?shop=${SHOP_ID}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setMenu)
      .catch(() => setError(true))
  }, [])

  const byCategory = useMemo(() => {
    const groups = {}
    for (const item of menu?.items ?? []) (groups[item.category] ??= []).push(item)
    return groups
  }, [menu])

  const count = cart.reduce((n, line) => n + line.qty, 0)
  const total = cart.reduce((sum, line) => sum + linePrice(line) * line.qty, 0)

  function addToCart(line) {
    setCart((c) => [...c, { ...line, key: nextLineKey++ }])
    setSelected(null)
  }

  function jumpTo(category) {
    setActiveCategory(category)
    sectionRefs.current[category]?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  async function placeOrder(memberEmail) {
    const res = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        shopId: SHOP_ID,
        tableNo: TABLE_NO,
        channel: TABLE_NO ? 'dine_in' : 'takeaway',
        memberEmail: memberEmail || undefined,
        items: cart.map((l) => ({
          itemId: l.item.id, qty: l.qty, temperature: l.temperature, sweetness: l.sweetness, ice: l.ice,
        })),
      }),
    })
    if (!res.ok) throw new Error(`order failed: ${res.status}`)
    const data = await res.json()
    setPlaced(data)
    setCart([])
    setCartOpen(false)
  }

  if (placed) return <Confirmation t={t} order={placed} onDone={() => setPlaced(null)} />

  return (
    <div className="app">
      <header className="header">
        <img className="logo" src="/logo.svg" alt="蛇記冰室 Snake Kee Café" />
        <div className="header-text">
          <h1>{lang === 'zh' ? '蛇記冰室' : 'Snake Kee Café'}</h1>
          <p>
            {menu ? menu.shop.name[lang] : ' '}
            {' · '}
            {TABLE_NO ? `${t.table} ${TABLE_NO}` : t.takeaway}
          </p>
        </div>
        <button className="lang" onClick={() => setLang(lang === 'en' ? 'zh' : 'en')} aria-label="Switch language">
          {lang === 'en' ? '繁' : 'EN'}
        </button>
      </header>

      <nav className="tabs">
        {(menu?.categories ?? []).map((c) => (
          <button key={c.id} className={c.id === activeCategory ? 'tab active' : 'tab'} onClick={() => jumpTo(c.id)}>
            {t.categories[c.id]}
          </button>
        ))}
      </nav>

      <main className="menu">
        {error && <p className="notice">{t.error}</p>}
        {!menu && !error && <p className="notice">{t.loading}</p>}
        {menu?.categories.map((c) => (
          <section key={c.id} ref={(el) => (sectionRefs.current[c.id] = el)} className="section">
            <h2>{t.categories[c.id]}</h2>
            <div className="grid">
              {(byCategory[c.id] ?? []).map((item) => (
                <MenuItemCard key={item.id} item={item} lang={lang} t={t} onSelect={() => setSelected(item)} />
              ))}
            </div>
          </section>
        ))}
        {menu && <footer className="credits"><a href="/menu/credits.html">{t.photoCredits}</a></footer>}
      </main>

      {count > 0 && (
        <button className="cart-bar" onClick={() => setCartOpen(true)}>
          <span className="badge">{count}</span>
          <span>{t.viewOrder}</span>
          <span className="cart-total">{formatPrice(total)}</span>
        </button>
      )}

      {selected && (
        <ItemSheet item={selected} lang={lang} t={t} options={menu.options}
                   onAdd={addToCart} onClose={() => setSelected(null)} />
      )}
      {cartOpen && (
        <CartSheet t={t} lang={lang} cart={cart} total={total}
                   onRemove={(key) => setCart((c) => c.filter((l) => l.key !== key))}
                   onPlace={placeOrder} onClose={() => setCartOpen(false)} />
      )}
    </div>
  )
}
