"""Wipes the dev database and the R2 bucket so everyone can sign up again.

Deletes every row in every table (users, workspaces, voiceprints, meetings, everything) and every
object in R2. The schema and the migrations are not touched.

It prints what it would delete first. Nothing is deleted unless you pass --confirm.
It refuses to run when:
  - DEV_TOOLS_ENABLED is not true,
  - the database it would wipe is the same Supabase project as TEST_DATABASE_URL.

Run with:
    cd backend && uv run python ../scripts/reset_dev_data.py            (counts only, then refuses)
    cd backend && uv run python ../scripts/reset_dev_data.py --confirm  (really deletes)
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import text

from app.core import storage
from app.core.config import settings
from app.core.db import engine
from app.core.db_projects import describe, same_project
from app.models import Base


def test_database_url() -> str:
    from_environment = os.environ.get("TEST_DATABASE_URL")

    if from_environment:
        return from_environment

    backend_env = Path(__file__).resolve().parent.parent / "backend" / ".env"

    return dotenv_values(backend_env).get("TEST_DATABASE_URL") or ""


def reason_to_refuse(dev_tools_enabled: bool, target_url: str, test_url: str, confirmed: bool) -> str | None:
    """Returns why the reset must not run, or None when it may."""
    if not dev_tools_enabled:
        return "DEV_TOOLS_ENABLED is not true, so this reset will not run."

    if test_url and same_project(target_url, test_url):
        return "The database this would wipe is the same Supabase project as TEST_DATABASE_URL. Refusing."

    if not confirmed:
        return "Nothing was deleted. Pass --confirm to delete everything listed above."

    return None


def table_names() -> list[str]:
    return [table.name for table in Base.metadata.sorted_tables]


def count_rows() -> dict[str, int]:
    counts = {}

    with engine.connect() as connection:
        for name in table_names():
            counts[name] = connection.execute(text(f'select count(*) from "{name}"')).scalar_one()

    return counts


def count_objects() -> int:
    return len(storage.list_keys())


def print_counts(title: str, rows: dict[str, int], object_count: int) -> None:
    print(f"\n{title}")

    for name, count in rows.items():
        print(f"  {name:<22} {count}")

    print(f"  {'R2 objects':<22} {object_count}")


def wipe() -> None:
    # TRUNCATE ... CASCADE empties every table in one statement without caring about the order of
    # foreign keys. alembic_version is not in the models, so the migration history stays.
    names = ", ".join(f'"{name}"' for name in table_names())

    with engine.begin() as connection:
        connection.execute(text(f"truncate table {names} restart identity cascade"))

    storage.delete_prefix("")


def main() -> int:
    parser = argparse.ArgumentParser(description="Wipe the dev database and R2 bucket.")
    parser.add_argument("--confirm", action="store_true", help="really delete (without it, only counts are shown)")
    arguments = parser.parse_args()

    test_url = test_database_url()
    print(f"Target database: {describe(settings.database_url)}")
    print(f"Test database:   {describe(test_url) if test_url else '(TEST_DATABASE_URL not set)'}")
    print(f"R2 bucket:       {settings.r2_bucket_name}")

    # Safety first: when this would hit the wrong place, stop before even counting.
    unsafe = reason_to_refuse(settings.dev_tools_enabled, settings.database_url, test_url, confirmed=True)

    if unsafe:
        print(f"\n{unsafe}")

        return 2

    print_counts("Before", count_rows(), count_objects())

    if not arguments.confirm:
        print(f"\n{reason_to_refuse(True, settings.database_url, test_url, confirmed=False)}")

        return 2

    wipe()
    after_rows = count_rows()
    after_objects = count_objects()
    print_counts("After", after_rows, after_objects)

    if any(after_rows.values()) or after_objects:
        print("\nSomething was left behind. See the counts above.")

        return 1

    print("\nDone. Every table and the bucket are empty.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
