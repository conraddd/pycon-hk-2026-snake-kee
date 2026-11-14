# The demo: same code, same command, different data

Two rounds, about 6 minutes. Each round is the same move:
run the tests on Django's empty test database (green), then on a **branch of production** (red).

Timings below are from a rehearsal from Hong Kong to a workspace in `us-west-2`
(~150 ms per round trip; tests take ~17 s, mostly network). Seeded with `--scale 0.2` (~1.1M orders, ~690 MB).

## Before you start

```bash
git checkout main
uv run python -m snakekee.lakebase ensure              # warm up the dev branch
uv run python manage.py runserver                      # terminal 1
(cd frontend && npm run dev)                           # terminal 2 → http://localhost:5173/?shop=1&table=12
```

Optional warm-up in the app: order a milk tea and join 蛇記 Rewards as `ChanTaiMan@example.hk`.
He has **three** accounts in production; the points land on just one of them. That's round 1.

## Round 1: "One 蛇記 Rewards account per email" (≈ 3½ min)

**1. New git branch → new database branch** (≈ 9 s, the hook does it)
```bash
git checkout -b feat/one-member-per-email
```
```text
🌱 Creating Lakebase branch 'feat-one-member-per-email' from 'production' ...
✅ Branch 'feat-one-member-per-email' is ready (2.8s)
```

**2. The feature is one line** in `shop/models.py`:
```python
email = models.EmailField(null=True, blank=True, unique=True)  # one 蛇記 Rewards account per email
```
```bash
uv run python manage.py makemigrations shop -n one_member_per_email
```

**3. Stock Django: green** (≈ 30 s, so talk over it: "Django is building a brand-new, empty database from my migrations")
```bash
uv run python manage.py test shop
```
```text
Creating test database for alias 'default'...
Ran 7 tests ... OK
```

**4. Same tests on a copy of production: red** (≈ 9 s)
```bash
LAKEBASE=1 uv run python manage.py test shop
```
```text
Using existing test database for alias 'default'...
🌿 Lakebase branch 'feat-one-member-per-email': a copy of production data
✗ Your migrations fail on production data:
  IntegrityError: could not create unique index "customers_email_…_uniq"
  DETAIL:  Key (email)=(chantaiman@example.hk) is duplicated.
```
*"Same code, same tests, different data. Of course it's 陳大文: he signed up three times. Without this, I'd have found out at 12:30 on a Saturday, halfway through a deploy, at lunch rush."*

**5. The fix: merge duplicate members first** (prepared in `demo/`; ≈ 37 s to rerun)

*"Django wrote the schema half of this migration for me, and it's correct, but only for an empty database.
The data half is mine to write."*
```bash
cp demo/round-1/0002_one_member_per_email.py shop/migrations/   # replaces the generated migration
LAKEBASE=1 uv run python manage.py test shop
```
Show `shop/migrations/0002_one_member_per_email.py`: a `RunPython` that keeps the oldest account,
moves orders and points, then the same `AlterField` Django generated.
```text
    merged 402 duplicate members into 401 accounts
Ran 7 tests ... OK
```

**6. Production didn't notice** (live in the Lakebase SQL editor, ≈ 30 s)

Open the project in the Databricks UI → **Lakebase** → **SQL editor**. Pick the branch
`feat-one-member-per-email`, run this, then switch the branch picker to `production` and run it again:
```sql
SELECT c.id, c.email, c.name, c.points, count(o.id) AS orders
FROM customers c LEFT JOIN orders o ON o.customer_id = c.id
WHERE lower(trim(c.email)) = 'chantaiman@example.hk'
GROUP BY c.id ORDER BY c.id;
```
Branch: 1 account (#40001, 1645 pts, 37 orders). Production: still 3 accounts (#40001, #40002, #40003).
*"The fix ran on the branch. Production still has his three accounts. When the fix is ready, it ships through the normal migration."*

Fallback without the UI (≈ 5 s each):
```bash
uv run python manage.py members chantaiman                          # the branch
LAKEBASE_BRANCH=production uv run python manage.py members chantaiman # production
```

## Round 2: "The kitchen display only understands 3 sweetness levels" (≈ 1½ min)

```bash
git add -A && git commit -qm "one member per email"        # round 1 stays on its branch
git checkout -b feat/kitchen-contract main                  # ≈ 7 s, new Lakebase branch, from main
cp demo/round-2/data_contracts.py shop/tests/test_data_contracts.py
```
Show `shop/tests/test_data_contracts.py`: a short test of what the kitchen display assumes,
that every drink's sweetness is 正常, 少甜 or 走甜.

```bash
LAKEBASE=1 uv run python manage.py test shop.tests.test_data_contracts   # ≈ 12 s
```
```text
AssertionError: Kitchen display can't read these:
  {'半糖': 2226, 'no sugar': 2221, '少少甜': 2213, '少甜 ': 2175, 'Less Sweet': 2160, 'less': 2146}
```
*"Nobody would write a test for 少少甜, or 少甜 with a trailing space. Only real data knows they exist."*

Optional, in the SQL editor on `production`:
```sql
SELECT sweetness, count(*) AS order_lines
FROM order_items
WHERE sweetness NOT IN ('', '正常', '少甜', '走甜')
GROUP BY sweetness ORDER BY order_lines DESC;
```
The fix (a mapping plus a bulk update) is in `demo/round-2/0002_map_old_sweetness.py`; no need to show it.

## Reset after a rehearsal

```bash
git checkout -f main && git branch -D feat/one-member-per-email feat/kitchen-contract
git clean -fd shop/                     # removes copied files that were never committed
uv run python -m snakekee.lakebase delete feat-one-member-per-email
uv run python -m snakekee.lakebase delete feat-kitchen-contract
```
(Or just leave them: they expire after `LAKEBASE_BRANCH_TTL_HOURS`.)

## If something goes wrong on stage

| Problem | Do this |
|---|---|
| Wi-Fi is slow or down | Switch to the recorded run; or phone hotspot |
| Branch already exists from a rehearsal | `uv run python -m snakekee.lakebase reset` (fresh copy of production) |
| Step 5 still red after the fix | The generated migration got applied somewhere: `lakebase reset`, then rerun step 5 |
| `Invalid token` / auth errors | `databricks auth login --profile <yours>` then `rm -rf .lakebase` |
| First command after a pause is slow | The branch's compute sleeps after 5 idle minutes (`LAKEBASE_SUSPEND_MINUTES`); the next connection wakes it. Run `uv run python -m snakekee.lakebase info` just before you go on stage |
| Tests too slow | Run one class: `LAKEBASE=1 uv run python manage.py test shop.tests.test_ordering.RewardsTests` |

## The prepared files

Everything you'd otherwise type live is in [`demo/`](demo/README.md). Django never loads that folder,
so `main` is unchanged until you copy a file in.

| File | Used in | What it is |
|---|---|---|
| `demo/round-1/0002_one_member_per_email.py` | Round 1, step 5 | The `RunPython` that merges duplicate members, then the `AlterField` |
| `demo/round-2/data_contracts.py` | Round 2 | The data-contract test |
| `demo/round-2/0002_map_old_sweetness.py` | (not shown) | Round 2's fix: map the old POS values |
