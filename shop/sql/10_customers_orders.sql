-- 90 days of 蛇記冰室 traffic, generated inside Postgres (fast, even over a slow network).
-- Scale knob: snake_kee.scale (set by `manage.py seed --scale`).
--   1.0  -> ~200k members, ~5.5M orders, ~13.7M order lines
--   0.01 -> ~2k members,  ~55k orders
-- All data is synthetic. Emails use example.* domains only.

SET TIME ZONE 'Asia/Hong_Kong';
SELECT setseed(0.42);  -- same data every time you seed

-- ---------------------------------------------------------------- 蛇記 Rewards members
INSERT INTO customers (email, phone, name, joined_at, points)
SELECT CASE WHEN random() < 0.02 THEN NULL      -- some members never gave an email
            ELSE 'member' || g || '@' || (ARRAY['example.com', 'example.hk', 'example.org'])[1 + g % 3]
       END,
       '+852 ' || (50000000 + (g::bigint * 7919) % 49999999)::text,
       (ARRAY['Tai Man', 'Siu Ming', 'Ka Yan', 'Wing Sze', 'Chi Keung', 'Mei Ling', 'Ho Yin', 'Hiu Tung', 'Ka Ho', 'Wai Lam'])[1 + g % 10]
         || ' ' ||
       (ARRAY['Chan', 'Wong', 'Lee', 'Cheung', 'Lau', 'Ho', 'Ng', 'Leung', 'Lam', 'Tsang', 'Yip', 'Kwok'])[1 + (g / 10) % 12],
       now() - random() * interval '3 years',
       floor(random() * 2000)::int
FROM generate_series(1, greatest(1000, (200000 * current_setting('snake_kee.scale')::real)::int)) AS g;

-- ---------------------------------------------------------------- orders: hourly curve x shop traffic x weekend bump
WITH params AS (
    SELECT 200 * current_setting('snake_kee.scale')::real AS base,
           (SELECT min(id) FROM customers) AS min_cust,
           (SELECT max(id) FROM customers) AS max_cust
), hour_weights(hr, w) AS (
    VALUES (7, 0.6), (8, 1.0), (9, 0.9), (10, 0.6), (11, 0.8), (12, 2.0), (13, 1.9), (14, 1.0),
           (15, 1.3), (16, 1.0), (17, 0.6), (18, 0.9), (19, 0.8), (20, 0.5), (21, 0.3)
), slots AS (
    SELECT s.id AS shop_id, s.seats, d::date AS day, hw.hr,
           round(p.base * hw.w * s.traffic
                 * CASE WHEN extract(isodow FROM d) IN (6, 7) THEN 1.25 ELSE 1.0 END
                 * (0.85 + random() * 0.3))::int AS n
    FROM params p
    CROSS JOIN shops s
    CROSS JOIN generate_series(current_date - 90, current_date - 1, interval '1 day') AS d
    CROSS JOIN hour_weights hw
), raw AS (
    SELECT sl.shop_id, sl.seats, sl.day, sl.hr, p.min_cust, p.max_cust,
           random() AS r_cust, random() AS r_chan, random() AS r_tab, random() AS r_min
    FROM slots sl
    CROSS JOIN params p
    CROSS JOIN LATERAL generate_series(1, sl.n) AS g
    OFFSET 0                                     -- fence: evaluate random() once per row
)
INSERT INTO orders (shop_id, customer_id, table_no, channel, status, ordered_at, total)
SELECT shop_id,
       CASE WHEN r_cust < 0.35 THEN min_cust + floor(r_cust / 0.35 * (max_cust - min_cust + 1))::bigint END,
       CASE WHEN r_chan < 0.75 THEN 1 + floor(r_tab * greatest(1, seats / 3))::int END,
       CASE WHEN r_chan < 0.75 THEN 'dine_in' ELSE 'takeaway' END,
       'paid',
       (day + make_interval(hours => hr))::timestamptz + r_min * interval '1 hour',
       0
FROM raw;

-- ---------------------------------------------------------------- order lines: 1-4 per order, weighted by popularity
WITH pool AS (
    SELECT array_agg(id ORDER BY id) AS ids
    FROM menu_items, generate_series(1, popularity)
), lines AS (
    SELECT o.id AS order_id,
           (SELECT ids FROM pool)[1 + floor(random() * (SELECT cardinality(ids) FROM pool))::int] AS item_id,
           random() AS r_temp, random() AS r_sweet, random() AS r_ice, random() AS r_qty
    FROM orders o
    CROSS JOIN LATERAL generate_series(1, 1 + (hashtext(o.id::text) & 3)) AS l(line_no)
    OFFSET 0
), shaped AS (
    SELECT li.*, m.category, m.price, m.iced_surcharge, m.iced_only,
           CASE WHEN m.category <> 'drink' THEN ''
                WHEN m.iced_only THEN 'iced'
                WHEN m.iced_surcharge IS NOT NULL AND li.r_temp < 0.55 THEN 'iced'
                ELSE 'hot' END AS temperature
    FROM lines li JOIN menu_items m ON m.id = li.item_id
)
INSERT INTO order_items (order_id, item_id, qty, unit_price, temperature, sweetness, ice)
SELECT order_id, item_id,
       CASE WHEN r_qty < 0.1 THEN 2 ELSE 1 END,
       price + CASE WHEN temperature = 'iced' THEN coalesce(iced_surcharge, 0) ELSE 0 END,
       temperature,
       CASE WHEN category <> 'drink' THEN ''
            WHEN r_sweet < 0.55 THEN '正常' WHEN r_sweet < 0.90 THEN '少甜' ELSE '走甜' END,
       CASE WHEN temperature <> 'iced' THEN ''
            WHEN r_ice < 0.75 THEN '正常冰' WHEN r_ice < 0.92 THEN '少冰' ELSE '走冰' END
FROM shaped;

-- ---------------------------------------------------------------- order totals
UPDATE orders o
SET total = t.total
FROM (SELECT order_id, sum(qty * unit_price) AS total FROM order_items GROUP BY order_id) t
WHERE o.id = t.order_id;
