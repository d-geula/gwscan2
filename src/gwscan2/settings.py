from pathlib import Path


BASE_URL = "https://main.gatewa.rs"
COMMAND_CENTER_URL = BASE_URL + "/base.php"
BATTLEFIELD_URL = BASE_URL + "/battlefield.php?page="
PROFILE_STATS_URL = BASE_URL + "/stats.php?id="
REFERER = COMMAND_CENTER_URL + "?game=gatewars"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "players.sqlite3"

PROFILE_DIR = PROJECT_ROOT / "profile"
