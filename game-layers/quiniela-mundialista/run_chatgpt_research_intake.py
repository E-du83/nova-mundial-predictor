import argparse

from chatgpt_research_intake_engine import (
    INTAKE_PACKAGE_PATH,
    ensure_chatgpt_research_intake_template,
    load_chatgpt_research_package,
    split_chatgpt_package_to_fixture_and_research,
    validate_chatgpt_research_package,
    write_intake_artifacts,
)
from worldcup_2026_fixture_guard import evaluate_group_stage_simulation_readiness
from worldcup_2026_fixture_snapshot_importer import import_fixture_snapshot


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate ChatGPT research intake package.")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply-fixture-import", action="store_true")
    return parser


def run_chatgpt_research_intake(apply_fixture_import: bool = False) -> dict:
    ensure_chatgpt_research_intake_template(INTAKE_PACKAGE_PATH)
    package = load_chatgpt_research_package(INTAKE_PACKAGE_PATH)
    validation = validate_chatgpt_research_package(package)
    split = split_chatgpt_package_to_fixture_and_research(package)
    paths = write_intake_artifacts(package, validation, split)

    dry_run_import = None
    apply_import = None
    if validation["fixture_ready"]:
        dry_run_import = import_fixture_snapshot(paths["fixture_snapshot"], dry_run=True)
        if apply_fixture_import and dry_run_import.get("import_status") == "dry_run_ok":
            apply_import = import_fixture_snapshot(paths["fixture_snapshot"], dry_run=False)

    guard = evaluate_group_stage_simulation_readiness()
    report = {
        "intake_status": validation["validation_status"],
        "fixture_ready": validation["fixture_ready"],
        "research_ready": validation["research_ready"],
        "matches_detected": validation["matches_detected"],
        "groups_detected": validation["groups_detected"],
        "teams_detected": validation["teams_detected"],
        "dry_run": True,
        "apply_fixture_import": bool(apply_fixture_import),
        "fixture_import_dry_run": dry_run_import or {"import_status": "not_run"},
        "fixture_import_apply": apply_import or {"import_status": "not_run"},
        "guard_status": guard.get("guard_status", "missing"),
        "ready_for_full_group_simulation": guard.get("ready_for_full_group_simulation", False),
        "paths": paths,
        "errors": validation["errors"],
        "warnings": validation["warnings"],
        "missing_data": validation["missing_data"],
        "next_steps": [
            "Fill fixture.matches with 72 official group-stage matches if intake_status is missing_or_template.",
            "Run intake in dry-run until fixture_ready=true and fixture import dry-run passes.",
            "Use --apply-fixture-import only after source_status=official_verified and source review is complete.",
            "Run emergency quiniela fill after Fixture Guard reports ready.",
        ],
    }
    return report


def main() -> None:
    args = _parser().parse_args()
    report = run_chatgpt_research_intake(apply_fixture_import=args.apply_fixture_import)
    print("NOVA CHATGPT RESEARCH INTAKE")
    print(f"- package path: {INTAKE_PACKAGE_PATH}")
    print(f"- intake status: {report['intake_status']}")
    print(f"- fixture ready: {str(report['fixture_ready']).lower()}")
    print(f"- research ready: {str(report['research_ready']).lower()}")
    print(f"- matches detected: {report['matches_detected']}")
    print(f"- groups detected: {report['groups_detected']}")
    print(f"- teams detected: {report['teams_detected']}")
    print(f"- fixture import dry-run: {report['fixture_import_dry_run']['import_status']}")
    print(f"- fixture import apply: {report['fixture_import_apply']['import_status']}")
    print(f"- guard status: {report['guard_status']}")
    print(f"- ready for full group simulation: {str(report['ready_for_full_group_simulation']).lower()}")
    print("Report paths:")
    for key, value in report["paths"].items():
        print(f"- {key}: {value}")
    print("Warnings:")
    if report["warnings"]:
        for warning in report["warnings"]:
            print(f"- {warning}")
    else:
        print("- none")
    print("Missing data:")
    if report["missing_data"]:
        for item in report["missing_data"]:
            print(f"- {item}")
    else:
        print("- none")
    print("Next steps:")
    for item in report["next_steps"]:
        print(f"- {item}")


if __name__ == "__main__":
    main()
