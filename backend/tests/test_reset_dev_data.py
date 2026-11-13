"""The safety rules of scripts/reset_dev_data.py. No database is touched: only the refusal logic runs."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "reset_dev_data.py"
DEV_URL = "postgresql+psycopg://postgres.devprojectid:pw@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
TEST_URL = "postgresql+psycopg://postgres.testprojectid:pw@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres"


def load_script():
    spec = importlib.util.spec_from_file_location("reset_dev_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def test_it_refuses_without_dev_tools_enabled() -> None:
    reset = load_script()

    assert "DEV_TOOLS_ENABLED" in reset.reason_to_refuse(False, DEV_URL, TEST_URL, confirmed=True)


def test_it_refuses_when_the_target_is_the_test_project() -> None:
    reset = load_script()

    same_project_other_port = TEST_URL.replace(":5432", ":6543")

    assert "TEST_DATABASE_URL" in reset.reason_to_refuse(True, same_project_other_port, TEST_URL, confirmed=True)


def test_it_refuses_without_confirm_and_allows_a_confirmed_dev_reset() -> None:
    reset = load_script()

    assert "--confirm" in reset.reason_to_refuse(True, DEV_URL, TEST_URL, confirmed=False)
    assert reset.reason_to_refuse(True, DEV_URL, TEST_URL, confirmed=True) is None


def test_it_still_runs_when_no_test_database_is_configured() -> None:
    reset = load_script()

    assert reset.reason_to_refuse(True, DEV_URL, "", confirmed=True) is None
