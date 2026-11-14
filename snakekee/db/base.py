"""Django's built-in PostgreSQL backend + Lakebase OAuth.

The only difference from `django.db.backends.postgresql`: every new connection
gets the host of the current Lakebase branch and a fresh short-lived OAuth token
as its password
(see snakekee/lakebase.py). Everything else (ORM, migrations, test runner) is stock Django.
"""
from django.db.backends.postgresql import base

from snakekee import lakebase


class DatabaseWrapper(base.DatabaseWrapper):
    def get_connection_params(self):
        params = super().get_connection_params()
        params.update(lakebase.connection_params())
        return params
