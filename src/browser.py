import zendriver as zd

from settings import PROFILE_DIR


async def start_browser() -> zd.Browser:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return await zd.start(headless=False, user_data_dir=PROFILE_DIR)
