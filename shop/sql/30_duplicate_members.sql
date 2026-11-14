-- Real-world mess #1 (demo round 1): ~1% of 蛇記 Rewards members signed up twice.

-- 陳大文 (Chan Tai Man, Hong Kong's "John Doe") signed up three times.
-- His is the only EXACT duplicate, so a plain UNIQUE constraint fails, and names him.
INSERT INTO customers (email, phone, name, joined_at, points) VALUES
  ('chantaiman@example.hk',  '+852 9123 4567', 'Chan Tai Man 陳大文', now() - interval '2 years',  1200),
  ('chantaiman@example.hk',  '91234567',       '陳大文',              now() - interval '1 year',    300),
  ('ChanTaiMan@Example.hk ', '+85291234567',   'Chan Tai-man',        now() - interval '3 months',   50);

WITH src AS (
    SELECT id, email, phone, name, joined_at
    FROM customers
    WHERE email LIKE 'member%'
    ORDER BY random()
    LIMIT (SELECT greatest(10, count(*) / 100) FROM customers)
)
INSERT INTO customers (email, phone, name, joined_at, points)
SELECT CASE id % 3                  -- (only 陳大文 has an EXACT duplicate, so he's the one in the error)
         WHEN 0 THEN initcap(email)        -- Member123@Example.Com
         WHEN 1 THEN upper(email)          -- MEMBER123@EXAMPLE.COM
         ELSE email || ' '                 -- trailing space from copy-paste
       END,
       replace(phone, '+852 ', ''),
       name,
       least(now(), joined_at + random() * interval '200 days'),
       floor(random() * 500)::int
FROM src;

-- Every other order of an original member now belongs to their duplicate account.
UPDATE orders o
SET customer_id = d.id
FROM customers d
JOIN customers c ON lower(trim(c.email)) = lower(trim(d.email)) AND c.id < d.id
WHERE o.customer_id = c.id
  AND o.id % 2 = 0;

-- Give 陳大文's three accounts some order history (he's a regular).
WITH chan AS (
    SELECT array_agg(id ORDER BY id) AS ids FROM customers WHERE lower(trim(email)) = 'chantaiman@example.hk'
), picked AS (
    SELECT id, row_number() OVER () AS n FROM (
        SELECT id FROM orders WHERE customer_id IS NULL ORDER BY random() LIMIT 36) x
)
UPDATE orders o
SET customer_id = (SELECT ids[1 + (p.n % 3)::int] FROM chan)
FROM picked p
WHERE o.id = p.id;
