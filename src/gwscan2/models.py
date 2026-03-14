from dataclasses import dataclass

@dataclass
class RowPayload:
    name: str
    profile_link: str
    alliance: str
    pop_text: str
    has_pop_cell: bool