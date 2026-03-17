import zendriver as zd

from gwscan2.settings import PROFILE_DIR


async def start_browser(mode: bool = False) -> zd.Browser:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return await zd.start(headless=mode, user_data_dir=PROFILE_DIR)
