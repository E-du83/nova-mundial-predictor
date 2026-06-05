"""
Official FIFA 2026 bracket mapping module.

Status:
- Scaffold ready.
- Exact Annex C third-place combination table is NOT embedded yet.
- The current project still uses `knockout_simulator.py` generic bracket until Annex C is ingested.

Why:
The 2026 Round of 32 third-place mapping depends on which 8 of the 12 third-placed teams qualify.
FIFA's regulations include the official combination table. That table must be imported exactly before this module can be used in exact mode.

Rule:
Do not fake the official bracket.
"""

class OfficialBracketNotReadyError(Exception):
    pass


def validate_annex_c_table(table: dict) -> bool:
    """
    Validate the expected shape of the Annex C mapping.

    Expected:
    {
      "ABCDEFGH": {
        "1A": "3C",
        "1B": "3D",
        ...
      }
    }

    There should be 495 possible combinations for 8 qualifying third-place groups out of 12.
    """
    if not isinstance(table, dict):
        return False
    return len(table) == 495


def load_official_annex_c_table(path: str) -> dict:
    import json
    with open(path, "r", encoding="utf-8") as f:
        table = json.load(f)
    if not validate_annex_c_table(table):
        raise ValueError("Annex C table is missing or incomplete. Expected 495 combinations.")
    return table


def build_round_of_32_official(qualified_rows: list[dict], annex_c_table: dict | None = None) -> list[tuple[str, str]]:
    """
    Build official Round of 32 matchups.

    Not enabled until Annex C table is imported.
    """
    if annex_c_table is None:
        raise OfficialBracketNotReadyError(
            "Official bracket mode requires Annex C mapping table. "
            "Use generic knockout simulator until Annex C is imported."
        )

    raise NotImplementedError(
        "Official bracket construction is scaffolded but requires final mapping implementation."
    )