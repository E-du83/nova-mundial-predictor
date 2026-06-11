from __future__ import annotations

from collections import Counter

from worldcup_2026_bracket_builder import build_knockout_bracket
from worldcup_2026_bracket_guard import evaluate_bracket_readiness
from worldcup_2026_bracket_structure import build_bracket_slots, write_default_bracket_files


def main() -> None:
    write_default_bracket_files()
    guard = evaluate_bracket_readiness()
    projection = build_knockout_bracket(dry_run=True)
    slots = build_bracket_slots()["slots"]
    counts = Counter(slot["round"] for slot in slots)
    print("NOVA WORLD CUP 2026 BRACKET STATUS")
    print(f"- knockout structure: OK")
    print(f"- round of 32 slots: {counts['round_of_32']}")
    print(f"- round of 16 slots: {counts['round_of_16']}")
    print(f"- quarter-final slots: {counts['quarter_finals']}")
    print(f"- semi-final slots: {counts['semi_finals']}")
    print(f"- third-place slot: {counts['third_place']}")
    print(f"- final slot: {counts['final']}")
    print(f"- bracket guard status: {guard['bracket_guard_status']}")
    print(f"- ready for knockout projection: {str(guard['ready_for_knockout_projection']).lower()}")
    print(f"- ready for knockout picks: {str(guard['ready_for_knockout_picks']).lower()}")
    print(f"- third-place selector status: {guard['third_place_status']}")
    print(f"- third-place matrix status: {guard['third_place_matrix_status']}")
    print(f"- projection status: {projection['builder_status']}")
    print("Warnings:")
    if guard["warnings"]:
        for warning in guard["warnings"]:
            print(f"- {warning}")
    else:
        print("- none")
    print("Next steps:")
    print("- Load verified final group standings after group stage is complete.")
    print("- Verify FIFA third-place combination matrix before assigning R32 third-place slots.")
    print("- Keep knockout picks disabled until bracket guard is ready.")


if __name__ == "__main__":
    main()
