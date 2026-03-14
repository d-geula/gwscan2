from typing import TYPE_CHECKING

from gwscan2.models import RowPayload
from gwscan2.locators import battlefield_players_table

if TYPE_CHECKING:
    import zendriver as zd


async def read_row_payloads(tab: "zd.Tab") -> list[RowPayload]:
    row_payloads_raw = await tab.evaluate(battlefield_players_table)
    if not isinstance(row_payloads_raw, list):
        return []

    row_payloads: list[RowPayload] = []
    for row_payload in row_payloads_raw:
        if not isinstance(row_payload, dict):
            continue

        row_payloads.append(
            RowPayload(
                name=str(row_payload.get("name", "")),
                profile_link=str(row_payload.get("href", "")),
                alliance=str(row_payload.get("alliance", "")),
                pop_text=str(row_payload.get("pop_text", "")),
                has_pop_cell=bool(row_payload.get("has_pop_cell", False)),
            )
        )

    return row_payloads
