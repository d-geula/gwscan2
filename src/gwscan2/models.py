from dataclasses import dataclass


@dataclass
class PlayerRecord:
    id: int
    name: str
    alliance: str | None
    army_size: int | None
    army_size_visible: bool