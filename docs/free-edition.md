# Free Edition: idle endpoints

Databricks Free Edition disables a compute endpoint after a couple of days without connections. The
next query fails, but the branch and its data are still there.

Observed on 2026-11-26 with Databricks CLI v1.26.0: `production` was last active on 2026-11-23 and had
been disabled by the time it was queried again (Free Edition, `us-east-2`).

## Symptom

A query against the branch fails with:

```text
ERROR: The endpoint has been disabled. Enable it using the API and retry.
```

## Re-enable the endpoint

The endpoint id is usually `primary`:

```bash
databricks postgres update-endpoint \
  projects/<project-id>/branches/production/endpoints/primary \
  spec.disabled \
  --json '{"spec":{"disabled":false}}' \
  --profile snake-kee
```

Then retry the original command. No data is lost.

## Why this happens

Free Edition reclaims idle compute. It is a platform lifecycle behaviour, not a problem with the repo
or the database contents. Branches created for a git branch expire after `LAKEBASE_BRANCH_TTL_HOURS`
(default 24), so `production` is the branch you are likely to find disabled.
