from pathlib import Path
import os
from dotenv import load_dotenv


BASE_URL = "https://main.gatewa.rs"
COMMAND_CENTER_URL = BASE_URL + "/base.php"
BATTLEFIELD_URL = BASE_URL + "/battlefield.php?page="
PROFILE_STATS_URL = BASE_URL + "/stats.php?id="
REFERER = COMMAND_CENTER_URL + "?game=gatewars"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "players.sqlite3"

PROFILE_DIR = PROJECT_ROOT / "profile"

def load_credentials() -> tuple[str, str, str]:
    """Load credentials from .env file."""
    load_dotenv()
    username = os.getenv("GW_USERNAME", "").strip()
    email = os.getenv("GW_EMAIL", "").strip()
    password = os.getenv("GW_PASSWORD", "").strip()

    missing = [
        name
        for name, value in (
            ("GW_USERNAME", username),
            ("GW_EMAIL", email),
            ("GW_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required credentials in .env: {joined}")

    return username, email, password