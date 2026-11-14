// $22, but $22.5 if there are cents
export function formatPrice(n) {
  const value = Number(n)
  const decimals = Number.isInteger(value) ? 0 : 1
  return `$${value.toFixed(decimals)}`
}

// Unit price of a cart line: iced drinks cost a little more (unless they only come iced).
export function linePrice({ item, temperature }) {
  const base = Number(item.price)
  const iced = temperature === 'iced' && !item.icedOnly && item.icedSurcharge != null
  return base + (iced ? Number(item.icedSurcharge) : 0)
}

// The picture for a drink follows hot / iced when we have both.
export const imageFor = (item, temperature) => item.images?.[temperature] ?? item.image
