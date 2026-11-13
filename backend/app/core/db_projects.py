"""Tells Supabase projects apart, so a script or test run can never mix up the dev and test databases.

Supabase pooler URLs carry the project id in the user name (postgres.<project id>); direct URLs
carry it in the host (db.<project id>.supabase.co). Neither password nor full URL is ever returned.
"""

import re
from urllib.parse import urlparse


def project_id(database_url: str) -> str | None:
    parsed = urlparse(database_url)
    user = parsed.username or ""

    if "." in user:
        return user.split(".", 1)[1]

    from_host = re.match(r"db\.([a-z0-9]+)\.supabase\.co", parsed.hostname or "")

    return from_host.group(1) if from_host else None


def same_project(first_url: str, second_url: str) -> bool:
    first, second = project_id(first_url), project_id(second_url)

    # When an id cannot be read, fall back to comparing host and user, so "unknown" is never "different".
    if first is None or second is None:
        a, b = urlparse(first_url), urlparse(second_url)

        return (a.hostname, a.username) == (b.hostname, b.username)

    return first == second


def describe(database_url: str) -> str:
    """A safe one-line description for logs: host and project id, never the password."""
    parsed = urlparse(database_url)

    return f"project {project_id(database_url) or '?'} on {parsed.hostname}"
