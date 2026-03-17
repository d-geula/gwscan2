import asyncio
from typing import TYPE_CHECKING, TypedDict

from gwscan2.locators import BattlefieldLocators as bl, battlefield_players_table

if TYPE_CHECKING:
    import zendriver as zd


class RowPayload(TypedDict):
    # Raw row data returned from the browser before Python normalizes it.
    name: str
    href: str
    alliance: str
    pop_text: str
    has_pop_cell: bool


async def get_battlefield_table(
    tab: "zd.Tab",
    timeout: float = 10,
    settle_attempts: int = 4,
    settle_delay: float = 0.35,
) -> list[RowPayload]:
    loop = asyncio.get_running_loop()
    start_time = loop.time()

    while loop.time() - start_time < timeout:
        if await tab.query_selector(bl.PLAYER_LINK):
            break
        await tab.sleep(0.25)
    else:
        raise asyncio.TimeoutError("Timed out waiting for battlefield player rows")

    for attempt in range(settle_attempts):
        row_payloads = await extract_battlefield_table(tab)
        player_rows = [row for row in row_payloads if row["href"]]
        if player_rows and all(row["has_pop_cell"] for row in player_rows):
            return row_payloads

        if attempt < settle_attempts - 1:
            await tab.sleep(settle_delay)

    raise RuntimeError("Battlefield table did not finish loading")


async def extract_battlefield_table(tab: "zd.Tab") -> list[RowPayload]:
    row_payloads_raw = await tab.evaluate(battlefield_players_table)
    if not isinstance(row_payloads_raw, list):
        raise TypeError(f"Expected battlefield table payload to be a list, got {type(row_payloads_raw).__name__}")

    row_payloads: list[RowPayload] = []
    for index, row_payload in enumerate(row_payloads_raw):
        if not isinstance(row_payload, dict):
            raise TypeError(f"Expected battlefield row {index} to be a dict, got {type(row_payload).__name__}")

        row_payloads.append(
            {
                "name": row_payload["name"],
                "href": row_payload["href"],
                "alliance": row_payload["alliance"],
                "pop_text": row_payload["pop_text"],
                "has_pop_cell": row_payload["has_pop_cell"],
            }
        )

    return row_payloads
