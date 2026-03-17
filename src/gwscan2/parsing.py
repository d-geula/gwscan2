import re

from gwscan2.models import PlayerRecord
from gwscan2.site_actions.battlefield_actions import RowPayload


def parse_page_range(value: str) -> range:
    match = re.fullmatch(r"\s*(\d+)\s*[:\-]\s*(\d+)\s*", value)
    if not match:
        raise ValueError(
            "Invalid page range. Use START:END or START-END, for example 1001:2000."
        )

    start = int(match.group(1))
    end = int(match.group(2))

    if start <= 0 or end <= 0:
        raise ValueError("Page numbers must be positive integers.")
    if start > end:
        raise ValueError("Start page must be less than or equal to end page.")

    return range(start, end + 1)


def parse_player_id(profile_link: str) -> int:
    if not profile_link.startswith("stats.php?id="):
        raise ValueError(f"Invalid profile link: {profile_link}")

    return int(profile_link.split("=")[1])


def parse_reversed_value(value: str) -> int | None:
    digits_match = re.search(r"\d[\d,]*", value)
    if not digits_match:
        return None

    reversed_value = digits_match.group(0).replace(",", "")
    return int(reversed_value[::-1])


def parse_battlefield_table(row_payloads: list[RowPayload]) -> list[PlayerRecord]:
    players: list[PlayerRecord] = []
    for row in row_payloads:
        if not row["href"]:
            continue

        pop_visible = True
        pop_value = parse_reversed_value(row["pop_text"])
        if pop_value is None:
            pop_visible = False

        players.append(
            PlayerRecord(
                id=parse_player_id(row["href"]),
                name=row["name"],
                alliance=row["alliance"] or None,
                army_size=pop_value,
                army_size_visible=pop_visible,
            )
        )
    return players
