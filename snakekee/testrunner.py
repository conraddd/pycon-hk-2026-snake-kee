"""Django's test runner, with one switch.

    python manage.py test              -> stock Django: creates a brand-new EMPTY test database
    LAKEBASE=1 python manage.py test   -> uses this git branch's Lakebase branch (a copy of production)

With LAKEBASE=1 the test database IS the branch, and the runner always keeps it (keepdb):
Django prints "Using existing test database...", applies only your new migrations, and runs
each test inside a transaction that is rolled back. It never creates or drops a database.

Guard rails: it refuses to run against `production`, and refuses TransactionTestCase on a
branch (those tests empty every table afterwards).
"""
import sys
import unittest

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.test import TestCase, TransactionTestCase
from django.test.runner import DiscoverRunner

from snakekee import lakebase

RED, BOLD, RESET = "\033[31m", "\033[1m", "\033[0m"


def _tests(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from _tests(test)
        else:
            yield test


def _is_sql_error(error: DatabaseError) -> bool:
    """True for errors Postgres raised about our SQL or data; False for connection or login problems."""
    sqlstate = getattr(error.__cause__, "sqlstate", None)
    return bool(sqlstate) and not sqlstate.startswith(("08", "28"))  # 08 = connection, 28 = auth


class BranchAwareTestRunner(DiscoverRunner):
    def __init__(self, *args, **kwargs):
        self.on_branch = getattr(settings, "TEST_ON_BRANCH", False)
        if lakebase.resolve_branch_id() == lakebase.PRODUCTION:
            raise ImproperlyConfigured("Refusing to run tests against the production branch.")
        if self.on_branch:
            kwargs["keepdb"] = True  # the branch is the test database: never create or drop it
        # Stock mode: replace a leftover empty test_<db> from an interrupted run without prompting.
        kwargs["interactive"] = False
        super().__init__(*args, **kwargs)

    def build_suite(self, *args, **kwargs):
        suite = super().build_suite(*args, **kwargs)
        if self.on_branch:
            flushing = sorted({type(t).__name__ for t in _tests(suite)
                               if isinstance(t, TransactionTestCase) and not isinstance(t, TestCase)})
            if flushing:
                raise ImproperlyConfigured(
                    f"{', '.join(flushing)} would empty every table on the branch. Use TestCase with LAKEBASE=1.")
        return suite

    def setup_databases(self, **kwargs):
        if not self.on_branch:
            return super().setup_databases(**kwargs)
        print(f"🌿 Lakebase branch '{lakebase.resolve_branch_id()}': a copy of production data")
        try:
            return super().setup_databases(**kwargs)
        except DatabaseError as e:
            if self.verbosity >= 2 or not _is_sql_error(e):
                raise
            # Your new migrations failed on production data. Show the part that matters.
            print(f"\n{RED}{BOLD}✗ Your migrations fail on production data:{RESET}")
            print(f"{RED}  {type(e).__name__}: {str(e).strip()}{RESET}".replace("\n", "\n  "))
            print("\n  (run with -v 2 for the full traceback)")
            sys.exit(1)
