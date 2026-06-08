"""Test settings: fast and isolated, but schema-compatible with the app.

Run the suite with:

    python manage.py test --settings=storyteller.settings_test

It reuses the configured PostgreSQL backend (Django creates a dedicated
``test_*`` database that is destroyed afterwards), but switches to a fast
password hasher, turns DEBUG off and redirects uploads to a throwaway media
directory so the real ``media/`` folder is never touched.

Note: SQLite is intentionally NOT used here. The ``Story.author`` field has a
callable default (``get_default_author``) that queries the users table; on
SQLite the table-rebuild done during ``AlterField`` migrations evaluates that
default before the schema is complete, which breaks migrations. PostgreSQL
applies these migrations cleanly (as the dev database already does).
"""

import tempfile

from .settings import *  # noqa: F401,F403

# Hashing passwords with the production hasher is the slowest part of auth
# tests; MD5 is acceptable for tests only.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Never run tests in DEBUG (mirrors production error handling).
DEBUG = False

# Keep uploaded files out of the real media folder.
MEDIA_ROOT = tempfile.mkdtemp(prefix="storyteller-test-media-")

# Make sure no test accidentally hits the real Gemini endpoint.
GEMINI_API_KEY = ""
GEMINI_MODEL = "gemini-2.5-flash"

# Keep the test database empty: don't run the demo-data seeder (a post_migrate
# signal) so tests don't have to account for baseline stories/comments.
SEED_DEMO_DATA = False

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}
