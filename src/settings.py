from pathlib import Path


BASE_URL = "https://main.gatewa.rs"
COMMAND_CENTER_URL = BASE_URL + "/base.php"
BATTLEFIELD_URL = BASE_URL + "/battlefield.php?page="
PROFILE_STATS_URL = BASE_URL + "/stats.php?id="
REFERER = COMMAND_CENTER_URL + "?game=gatewars"

DB_PATH = Path.cwd().parent / "players.sqlite3"

PROFILE_DIR = Path.cwd().parent / "profile"


