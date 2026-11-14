-- Real-world mess #2 (demo round 2): before the QR ordering app, 蛇記 used an old POS
-- where staff typed sweetness as free text. ~4% of drink lines older than 60 days.

UPDATE order_items oi
SET sweetness = (ARRAY['less', 'Less Sweet', 'no sugar', '少甜 ', '少少甜', '半糖'])[1 + floor(random() * 6)::int]
FROM orders o, menu_items m
WHERE o.id = oi.order_id
  AND m.id = oi.item_id
  AND m.category = 'drink'
  AND o.ordered_at < now() - interval '60 days'
  AND random() < 0.04;
