from typing import TYPE_CHECKING, TypedDict

from gwscan2.locators import battlefield_players_table

if TYPE_CHECKING:
    import zendriver as zd


class RowPayload(TypedDict):
    # Raw row data returned from the browser before Python normalizes it.
    name: str
    href: str
    alliance: str
    pop_text: str
    has_pop_cell: bool


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
