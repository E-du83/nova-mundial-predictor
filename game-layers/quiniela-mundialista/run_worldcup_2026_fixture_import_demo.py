from pathlib import Path

from worldcup_2026_fixture_snapshot_importer import (
    IMPORT_REPORT_PATH,
    SNAPSHOT_TEMPLATE_PATH,
    ensure_official_fixture_snapshot_template,
    import_fixture_snapshot,
)
from worldcup_2026_match_slot_engine import GROUP_STAGE_FIXTURE_PATH


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main() -> None:
    ensure_official_fixture_snapshot_template(SNAPSHOT_TEMPLATE_PATH)
    before = _read_text(GROUP_STAGE_FIXTURE_PATH)
    report = import_fixture_snapshot(
        snapshot_path=SNAPSHOT_TEMPLATE_PATH,
        current_fixture_path=GROUP_STAGE_FIXTURE_PATH,
        output_fixture_path=GROUP_STAGE_FIXTURE_PATH,
        validation_report_path=IMPORT_REPORT_PATH,
        dry_run=True,
    )
    after = _read_text(GROUP_STAGE_FIXTURE_PATH)
    active_changed = before != after

    print("NOVA WORLD CUP 2026 FIXTURE IMPORT DEMO")
    print(f"- dry run: {str(report['dry_run']).lower()}")
    print(f"- snapshot status: {report['snapshot_validation_status']}")
    print(f"- matches in snapshot: {report['matches_in_snapshot']}")
    print(f"- matches valid: {report['matches_valid']}")
    print(f"- matches blocked: {report['matches_blocked']}")
    print(f"- would update: {report['would_update_matches']}")
    print(f"- import status: {report['import_status']}")
    print(f"- active fixture changed: {'yes' if active_changed else 'no'}")
    print(f"- ready after import: {str(report['ready_for_full_group_simulation_after_import']).lower()}")
    print("Warnings:")
    for warning in report["warnings"]:
        print(f"- {warning}")
    print("Errors:")
    for error in report["errors"]:
        print(f"- {error}")
    print("Next steps:")
    print("- Fill the snapshot with verified official FIFA fixture data.")
    print("- Set source_status=official_confirmed only after source and fields are verified.")
    print("- Run this importer again in dry_run before any real import.")


if __name__ == "__main__":
    main()
