"""The only Lakebase-specific code in this project.

It answers three questions for Django:
  1. Which Lakebase branch should this checkout use?  (git branch -> Lakebase branch)
  2. What is that branch's Postgres host?            (create the branch from `production` if needed)
  3. What password do I use?                         (a short-lived database credential from your Databricks login)

Command line (used by the git hook and by humans):
  uv run python -m snakekee.lakebase info            # show the resolved branch + host
  uv run python -m snakekee.lakebase ensure          # create the branch for this git branch if it doesn't exist
  uv run python -m snakekee.lakebase list            # list branches in the project
  uv run python -m snakekee.lakebase reset [BRANCH]  # throw a branch away, take a fresh copy of production
  uv run python -m snakekee.lakebase delete [BRANCH] # delete a branch (never `production`)

Configuration (environment variables, or a `.env` file in the repo root):
  LAKEBASE_PROJECT           Lakebase project id (required)
  LAKEBASE_BRANCH            force a branch id (e.g. "production" for the deployed app)
  LAKEBASE_SOURCE_BRANCH     branch that new branches are created from (default "production")
  LAKEBASE_BRANCH_TTL_HOURS  lifetime of auto-created branches (default 24)
  LAKEBASE_MIN_CU / LAKEBASE_MAX_CU  autoscaling range of a new branch's compute (default 0.5 / 2)
  LAKEBASE_SUSPEND_MINUTES   a new branch's compute scales to zero after this much inactivity (default 5)
  LAKEBASE_AUTO_CREATE       "0" to never create branches automatically (default "1")
  DATABRICKS_CONFIG_PROFILE  Databricks CLI profile to authenticate with (optional)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = REPO_ROOT / ".lakebase" / "cache.json"
REFRESH_MARGIN = 300  # get a new database credential 5 minutes before the old one expires

# git branches that share one long-lived development database branch
DEV_GIT_BRANCHES = {"main", "master", "develop"}
DEV_BRANCH_ID = "dev"
PRODUCTION = "production"

# Databricks Free Edition caps endpoints at 1 CU. Observed on a Free Edition workspace (2026-11-23):
#   Requested compute size (2.0 CU) exceeds the maximum allowed (1.0 CU) for this workspace tier.
# A new branch inherits valid defaults, so this error is not fatal.
FREE_EDITION_COMPUTE_ERRORS = {
    "exceeds the maximum allowed (1.0 cu)": "endpoints are capped at 1 CU",
}


def load_dotenv() -> None:
    """Tiny .env loader so we don't need python-dotenv. Variables already set in the environment win."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def project_id() -> str:
    pid = os.environ.get("LAKEBASE_PROJECT")
    if not pid or pid.startswith("<"):
        raise RuntimeError("Set LAKEBASE_PROJECT to your Lakebase project id (see .env.example).")
    return pid


@lru_cache(maxsize=1)
def client():
    from databricks.sdk import WorkspaceClient  # imported lazily: only needed when talking to Lakebase

    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE")
    return WorkspaceClient(profile=profile) if profile else WorkspaceClient()


# ---------------------------------------------------------------- 1. which branch?
def git_branch() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        return None if out == "HEAD" else out  # detached HEAD
    except (OSError, subprocess.CalledProcessError):
        return None


def to_branch_id(git_name: str) -> str:
    """git branch name -> Lakebase branch id (1-63 chars: lowercase letters, digits, hyphens; starts with a letter).

    feat/one-member-per-email -> feat-one-member-per-email
    If the name can't be kept as is (e.g. 中文 characters, or `feat/x` vs `feat-x`), a short hash
    of the original name is added so different git branches never share a database branch.
    """
    slug = re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", git_name.lower())).strip("-")
    if not slug or not slug[0].isalpha():
        slug = f"b-{slug}".rstrip("-")
    lossless = slug == git_name.replace("/", "-")  # only `/` became `-`
    if not lossless or len(slug) > 63:
        slug = f"{slug[:56].rstrip('-')}-{hashlib.sha1(git_name.encode()).hexdigest()[:6]}"
    return slug


def resolve_branch_id() -> str:
    if forced := os.environ.get("LAKEBASE_BRANCH"):
        return forced
    git = git_branch()
    if git is None or git in DEV_GIT_BRANCHES:
        return DEV_BRANCH_ID
    return to_branch_id(git)


# ---------------------------------------------------------------- 2. which host?
def branch_path(branch_id: str) -> str:
    """Resource path of a branch in the Databricks API."""
    return f"projects/{project_id()}/branches/{branch_id}"


def branch_exists(branch_id: str) -> bool:
    from databricks.sdk.errors import NotFound

    try:
        client().postgres.get_branch(name=branch_path(branch_id))
        return True
    except NotFound:
        return False


def ensure_branch(branch_id: str, *, quiet: bool = False) -> bool:
    """Create `branch_id` as a copy-on-write copy of the source branch, if it doesn't exist yet.

    Returns True if it was created. The branch deletes itself after LAKEBASE_BRANCH_TTL_HOURS.
    """
    from databricks.sdk.service import postgres as pg
    from google.protobuf.duration_pb2 import Duration

    if branch_id == PRODUCTION or branch_exists(branch_id):
        return False
    source = os.environ.get("LAKEBASE_SOURCE_BRANCH", PRODUCTION)
    ttl = Duration()
    ttl.FromTimedelta(timedelta(hours=float(os.environ.get("LAKEBASE_BRANCH_TTL_HOURS", "24"))))
    t0 = time.monotonic()
    if not quiet:
        print(f"🌱 Creating Lakebase branch '{branch_id}' from '{source}' ...", flush=True)
    client().postgres.create_branch(
        parent=f"projects/{project_id()}",
        branch_id=branch_id,
        branch=pg.Branch(spec=pg.BranchSpec(source_branch=branch_path(source), ttl=ttl)),
    ).wait()
    endpoint, _ = _endpoint(branch_id, refresh=True)  # wait until its compute has a host
    size_compute(endpoint)
    if not quiet:
        print(f"✅ Branch '{branch_id}' is ready ({time.monotonic() - t0:.1f}s)", flush=True)
    return True


def size_compute(endpoint: str) -> None:
    """Keep a branch's compute small and sleepy: autoscale between LAKEBASE_MIN_CU and LAKEBASE_MAX_CU,
    and scale to zero after LAKEBASE_SUSPEND_MINUTES without connections.

    New branches otherwise inherit the project's default compute settings. On Databricks Free
    Edition, endpoints are capped at 1 CU; a new branch inherits valid defaults, so that error
    keeps the defaults instead of failing. This calls the REST API directly: the SDK's
    update_endpoint sends the field mask in camelCase, which the API rejects. Other errors still
    propagate.
    """
    from databricks.sdk.errors import BadRequest

    min_cu = float(os.environ.get("LAKEBASE_MIN_CU", "0.5"))
    max_cu = float(os.environ.get("LAKEBASE_MAX_CU", "2"))
    suspend = round(float(os.environ.get("LAKEBASE_SUSPEND_MINUTES", "5")) * 60)
    fields = ("autoscaling_limit_min_cu", "autoscaling_limit_max_cu", "suspend_timeout_duration")
    try:
        client().api_client.do(
            "PATCH", f"/api/2.0/postgres/{endpoint}",
            query={"update_mask": ",".join(f"spec.{f}" for f in fields)},
            body={"name": endpoint, "spec": {
                "endpoint_type": "ENDPOINT_TYPE_READ_WRITE",
                "autoscaling_limit_min_cu": min_cu,
                "autoscaling_limit_max_cu": max_cu,
                "suspend_timeout_duration": f"{suspend}s",
            }},
        )
    except BadRequest as err:
        message = str(err).lower()
        limit = next((why for text, why in FREE_EDITION_COMPUTE_ERRORS.items() if text in message),
                     None)
        if limit is None:
            raise
        print(f"⚠️  Databricks Free Edition: {limit}; keeping the branch's defaults ({err})",
              flush=True)


@dataclass(frozen=True)
class Target:
    branch_id: str
    endpoint: str  # resource path of the branch's compute
    host: str      # Postgres host name
    user: str      # Postgres role


def _read_cache() -> dict:
    try:
        return json.loads(CACHE_FILE.read_text())
    except (OSError, ValueError):
        return {}


def _write_cache(data: dict) -> None:
    """The cache holds short-lived database passwords: readable by you only, written atomically."""
    CACHE_FILE.parent.mkdir(exist_ok=True)
    tmp = CACHE_FILE.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, CACHE_FILE)


def _endpoint(branch_id: str, *, refresh: bool = False) -> tuple[str, str]:
    """(endpoint path, host) of the branch's read-write compute. Cached per branch."""
    from databricks.sdk.service import postgres as pg

    cache = _read_cache()
    key = f"{project_id()}/{branch_id}"
    if not refresh and key in cache.get("endpoints", {}):
        e = cache["endpoints"][key]
        return e["endpoint"], e["host"]
    for _ in range(120):  # a brand-new branch may need a few seconds to get a host
        eps = list(client().postgres.list_endpoints(parent=branch_path(branch_id)))
        rw = [e for e in eps if e.status and e.status.endpoint_type == pg.EndpointType.ENDPOINT_TYPE_READ_WRITE]
        ep = (rw or eps or [None])[0]
        if ep and ep.status and ep.status.hosts and ep.status.hosts.host:
            cache.setdefault("endpoints", {})[key] = {"endpoint": ep.name, "host": ep.status.hosts.host}
            _write_cache(cache)
            return ep.name, ep.status.hosts.host
        time.sleep(1)
    raise RuntimeError(f"Branch '{branch_id}' has no read-write endpoint with a host.")


@lru_cache(maxsize=1)
def db_user() -> str:
    """Postgres role = your Databricks identity (email for users, client id for service principals)."""
    if user := os.environ.get("LAKEBASE_USER"):
        return user
    if client_id := os.environ.get("DATABRICKS_CLIENT_ID"):  # e.g. inside a Databricks App
        return client_id
    return client().current_user.me().user_name


def target(branch_id: str | None = None) -> Target:
    branch_id = branch_id or resolve_branch_id()
    key = f"{project_id()}/{branch_id}"
    if key not in _read_cache().get("endpoints", {}) and os.environ.get("LAKEBASE_AUTO_CREATE", "1") == "1":
        ensure_branch(branch_id)  # first use of this git branch: create its Lakebase branch
    endpoint, host = _endpoint(branch_id)
    return Target(branch_id=branch_id, endpoint=endpoint, host=host, user=db_user())


# ---------------------------------------------------------------- 3. which password?
def db_password(endpoint: str) -> str:
    """The Postgres password: a short-lived database credential (OAuth token) for `endpoint`.

    Generated from your Databricks login, cached on disk until shortly before it expires (about 1 hour).
    """
    cache = _read_cache()
    entry = cache.get("credentials", {}).get(endpoint)
    if entry and entry["expires"] - REFRESH_MARGIN > time.time():
        return entry["password"]
    cred = client().postgres.generate_database_credential(endpoint=endpoint)
    expires = time.time() + 3600
    if cred.expire_time is not None:
        try:
            expires = cred.expire_time.ToSeconds()
        except AttributeError:
            pass
    cache.setdefault("credentials", {})[endpoint] = {"password": cred.token, "expires": expires}
    _write_cache(cache)
    return cred.token


def _forget(branch_id: str) -> None:
    cache = _read_cache()
    cache.get("endpoints", {}).pop(f"{project_id()}/{branch_id}", None)
    _write_cache(cache)


def connection_params() -> dict:
    """host / user / password for the current branch. Recovers if a cached branch has expired (TTL)."""
    from databricks.sdk.errors import NotFound

    t = target()
    try:
        password = db_password(t.endpoint)
    except NotFound:  # the branch expired or was deleted since we cached it
        _forget(t.branch_id)
        t = target()
        password = db_password(t.endpoint)
    return {"host": t.host, "user": t.user, "password": password}


# ---------------------------------------------------------------- CLI
def _cli(argv: list[str]) -> int:
    load_dotenv()
    cmd, args = (argv[0], [a for a in argv[1:] if not a.startswith("-")]) if argv else ("info", [])
    branch_id = args[0] if args else resolve_branch_id()
    if cmd == "info":
        t = target()
        print(f"git branch      : {git_branch()}")
        print(f"lakebase branch : {t.branch_id}")
        print(f"host            : {t.host}")
        print(f"user            : {t.user}")
    elif cmd == "ensure":
        created = ensure_branch(branch_id)
        if not created and "--quiet" not in argv:
            print(f"✅ Lakebase branch '{branch_id}' already exists")
        _endpoint(branch_id, refresh=True)
    elif cmd == "list":
        for b in client().postgres.list_branches(parent=f"projects/{project_id()}"):
            exp = b.status.expire_time.ToDatetime().isoformat() if b.status and b.status.expire_time else "never"
            size = ""
            for e in client().postgres.list_endpoints(parent=b.name):
                st = e.status
                if st and st.autoscaling_limit_max_cu:
                    sleep = st.suspend_timeout_duration.ToTimedelta() if st.suspend_timeout_duration else None
                    size = (f"  compute: {st.autoscaling_limit_min_cu:g}-{st.autoscaling_limit_max_cu:g} CU, "
                            f"sleeps after {sleep or 'never'}")
            print(f"{b.name.rsplit('/', 1)[-1]:<32} expires: {exp:<28}{size}")
    elif cmd in ("reset", "delete"):
        if branch_id == PRODUCTION:
            print(f"Refusing to {cmd} '{PRODUCTION}'. Use the Databricks UI if you really mean it.")
            return 1
        if branch_exists(branch_id):
            client().postgres.delete_branch(name=branch_path(branch_id)).wait()
        _forget(branch_id)
        if cmd == "reset":
            ensure_branch(branch_id)
        else:
            print(f"🗑  Deleted Lakebase branch '{branch_id}'")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
