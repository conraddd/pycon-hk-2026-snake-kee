"""Deploy 蛇記冰室 as a Databricks App, connected to the `production` branch of your Lakebase project.

    uv run python scripts/deploy_app.py            # create (first time) + deploy
    uv run python scripts/deploy_app.py --name my-snake-kee

What it does:
  1. creates the app with a Lakebase resource (gives the app's service principal a Postgres role)
  2. grants that role access to the shop tables (they're owned by you, who ran `migrate`)
  3. sets LAKEBASE_PROJECT in app.yaml to your project (from .env)
  4. uploads this folder to your workspace (respects .gitignore) and deploys it
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from databricks.sdk.service import apps  # noqa: E402

from snakekee import lakebase  # noqa: E402

lakebase.load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="snake-kee")
    args = parser.parse_args()
    w = lakebase.client()
    project = lakebase.project_id()
    branch = f"projects/{project}/branches/production"
    database = f"{branch}/databases/databricks-postgres"

    # 1. the app + its Lakebase resource
    existing = {a.name for a in w.apps.list()}
    if args.name not in existing:
        print(f"Creating app '{args.name}' (a few minutes) ...", flush=True)
        w.apps.create_and_wait(apps.App(
            name=args.name,
            description="蛇記冰室 Snake Kee Café: QR ordering on Lakebase (PyCon HK 2026 demo)",
            resources=[apps.AppResource(
                name="lakebase",
                postgres=apps.AppResourcePostgres(
                    branch=branch, database=database,
                    permission=apps.AppResourcePostgresPostgresPermission.CAN_CONNECT_AND_CREATE))],
        ))
    app = w.apps.get(args.name)
    sp = app.service_principal_client_id
    print(f"App service principal: {sp}")

    # 2. table access for the app's role (tables were created by you via `migrate`)
    import psycopg

    t = lakebase.target("production")
    with psycopg.connect(host=t.host, dbname="databricks_postgres", user=t.user,
                         password=lakebase.db_password(t.endpoint), sslmode="require", autocommit=True) as conn:
        # Only what the ordering app needs (read the menu, write orders and members), now and for
        # tables that future migrations create.
        for stmt in (
            f'GRANT USAGE ON SCHEMA public TO "{sp}"',
            f'GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO "{sp}"',
            f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{sp}"',
            f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE ON TABLES TO "{sp}"',
            f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "{sp}"',
        ):
            conn.execute(stmt)
    print("Granted table access on 'production'")

    # 3. the app must connect to *your* project: keep app.yaml in sync with .env
    app_yaml = REPO / "app.yaml"
    text = app_yaml.read_text()
    synced = re.sub(r"(- name: LAKEBASE_PROJECT\n\s+value: ).*", rf"\g<1>{project}", text)
    if synced != text:
        app_yaml.write_text(synced)
        print(f"Updated app.yaml: LAKEBASE_PROJECT={project}")

    # 4. upload + deploy
    me = w.current_user.me().user_name
    target = f"/Workspace/Users/{me}/apps/{args.name}"
    profile = ["--profile", lakebase.os.environ["DATABRICKS_CONFIG_PROFILE"]] \
        if lakebase.os.environ.get("DATABRICKS_CONFIG_PROFILE") else []
    subprocess.run(["databricks", "sync", str(REPO), target, *profile], check=True)
    print(f"Deploying from {target} ...", flush=True)
    dep = w.apps.deploy_and_wait(args.name, apps.AppDeployment(source_code_path=target))
    print(f"Deployment: {dep.status.state.value if dep.status else '?'} - {dep.status.message if dep.status else ''}")
    print(f"Open: {w.apps.get(args.name).url}")


if __name__ == "__main__":
    main()
