# Prepared files for the live demo

Django never loads anything in this folder (it isn't in `shop/migrations/` or `shop/tests/`),
so `main` stays exactly as it is. On stage you copy a file in at the right moment.

| File | Round | Copy it to |
|---|---|---|
| `round-1/0002_one_member_per_email.py` | 1, the fix | `shop/migrations/` (replaces the generated migration) |
| `round-2/data_contracts.py` | 2, the test | `shop/tests/test_data_contracts.py` |
| `round-2/0002_map_old_sweetness.py` | 2, the fix (optional) | `shop/migrations/` |

The full stage script, with expected output and timings, is in [`../DEMO.md`](../DEMO.md).
