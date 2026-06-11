from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from group_context_engine import (
    build_group_context,
    calculate_points_pressure,
    detect_jornada3_trap,
)
from worldcup_2026_fixture_loader import load_worldcup_2026_fixture


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"
REPORT_PATH = DATA_ROOT / "worldcup_2026_group_context_report.json"
GUARD_REPORT_PATH = DATA_ROOT / "worldcup_2026_group_context_guard_report.json"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json_if_changed(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        comparable_existing = dict(existing)
        comparable_data = dict(data)
        comparable_existing.pop("generated_at", None)
        comparable_data.pop("generated_at", None)
        if comparable_existing == comparable_data:
            return
    path.write_text(text, encoding="utf-8")


def _synthetic_baseline() -> dict:
    return {
        "Synthetic Alpha": {
            "nova_strength_rating_v1": 1900,
            "fifa_rank": 5,
            "attack": 88,
            "defense": 86,
            "form": 1.03,
        },
        "Synthetic Beta": {
            "nova_strength_rating_v1": 1850,
            "fifa_rank": 11,
            "attack": 85,
            "defense": 84,
            "form": 1.01,
        },
        "Synthetic Gamma": {
            "nova_strength_rating_v1": 1785,
            "fifa_rank": 22,
            "attack": 82,
            "defense": 81,
            "form": 0.99,
        },
        "Synthetic Delta": {
            "nova_strength_rating_v1": 1700,
            "fifa_rank": 38,
            "attack": 78,
            "defense": 77,
            "form": 1.08,
        },
    }


def build_demo_report() -> dict:
    fixture_bundle = load_worldcup_2026_fixture()
    real_fixture = fixture_bundle["fixture"].get("matches", [])
    real_context = build_group_context(
        "A",
        ["pending_group_draw", "pending_group_draw", "pending_group_draw", "pending_group_draw"],
        {},
        fixtures=real_fixture,
        mode="pre_tournament",
    )

    synthetic_teams = _synthetic_baseline()
    original_synthetic = copy.deepcopy(synthetic_teams)
    synthetic_match = {
        "match_id": "SYN-H-06",
        "group": "Synthetic H",
        "matchday": 3,
        "team_a": "Synthetic Gamma",
        "team_b": "Synthetic Delta",
    }
    standings_must_win = {
        "Synthetic Alpha": {"points": 4, "played": 2},
        "Synthetic Beta": {"points": 4, "played": 2},
        "Synthetic Gamma": {"points": 3, "played": 2},
        "Synthetic Delta": {"points": 1, "played": 2},
    }
    synthetic_context = build_group_context(
        "Synthetic H",
        list(synthetic_teams),
        synthetic_teams,
        fixtures=[synthetic_match],
        standings_before_match=standings_must_win,
        match=synthetic_match,
        mode="synthetic_controlled",
    )
    trap_standings = {
        "Synthetic Alpha": {"points": 4, "played": 2},
        "Synthetic Beta": {"points": 4, "played": 2},
        "Synthetic Gamma": {"points": 2, "played": 2},
        "Synthetic Delta": {"points": 1, "played": 2},
    }
    synthetic_trap = detect_jornada3_trap(
        "Synthetic Alpha",
        "Synthetic Beta",
        trap_standings,
        matchday=3,
    )
    synthetic_pressure = calculate_points_pressure(
        "Synthetic Gamma",
        "Synthetic Delta",
        standings_must_win,
        3,
    )
    baseline_mutated = synthetic_teams != original_synthetic
    validation = {
        "real_context_placeholder_blocked": real_context["context_status"] == "placeholder_blocked",
        "real_context_allowed_for_prediction": real_context["allowed_for_prediction"],
        "real_context_has_no_flags": real_context["flags"] == [],
        "synthetic_death_or_strong_group": (
            synthetic_context["death_group_analysis"]["is_death_group"]
            or synthetic_context["group_strength"]["group_strength_bucket"] in ("elite", "strong")
        ),
        "synthetic_surprise_candidate": synthetic_context["surprise_candidate_analysis"][
            "has_surprise_candidate"
        ],
        "synthetic_jornada3_trap_confirmed": synthetic_trap["trap_confirmed"],
        "synthetic_must_win_pressure": synthetic_pressure["pressure_bucket"] == "high",
        "synthetic_baseline_mutated": baseline_mutated,
        "leakage_guard_ok": (
            real_context["leakage_guard"]["no_future_results"]
            and synthetic_context["leakage_guard"]["no_future_results"]
            and synthetic_context["leakage_guard"]["no_final_table_before_match"]
        ),
    }
    return {
        "data_status": "worldcup_2026_group_context_demo_v1",
        "generated_at": _now(),
        "real_context": real_context,
        "synthetic_context": synthetic_context,
        "synthetic_jornada3_trap": synthetic_trap,
        "synthetic_points_pressure": synthetic_pressure,
        "validation": validation,
    }


def main() -> None:
    report = build_demo_report()
    guard_report = {
        "generated_at": _now(),
        "real_fixture_context_status": report["real_context"]["context_status"],
        "real_allowed_for_prediction": report["real_context"]["allowed_for_prediction"],
        "placeholder_guard_ok": report["validation"]["real_context_placeholder_blocked"],
        "synthetic_validation_ok": (
            report["validation"]["real_context_placeholder_blocked"]
            and report["validation"]["real_context_allowed_for_prediction"] is False
            and report["validation"]["real_context_has_no_flags"]
            and report["validation"]["synthetic_death_or_strong_group"]
            and report["validation"]["synthetic_surprise_candidate"]
            and report["validation"]["synthetic_jornada3_trap_confirmed"]
            and report["validation"]["synthetic_must_win_pressure"]
            and report["validation"]["synthetic_baseline_mutated"] is False
            and report["validation"]["leakage_guard_ok"]
        ),
        "synthetic_baseline_mutated": report["validation"]["synthetic_baseline_mutated"],
        "prediction_impact_enabled": False,
    }
    _write_json_if_changed(REPORT_PATH, report)
    _write_json_if_changed(GUARD_REPORT_PATH, guard_report)

    print("NOVA GROUP CONTEXT DEMO")
    print("")
    print("Escenario real:")
    print(f"- context status: {report['real_context']['context_status']}")
    print(f"- allowed for prediction: {str(report['real_context']['allowed_for_prediction']).lower()}")
    print("- warning: " + "; ".join(report["real_context"]["warnings"]))
    print("")
    print("Escenario sintetico:")
    print(
        "- group strength: "
        + report["synthetic_context"]["group_strength"]["group_strength_bucket"]
    )
    print(
        "- death group: "
        + str(report["synthetic_context"]["death_group_analysis"]["is_death_group"]).lower()
    )
    print(
        "- surprise candidate: "
        + str(report["synthetic_context"]["surprise_candidate_analysis"]["surprise_team"])
    )
    print(
        "- jornada3 trap: "
        + str(report["synthetic_jornada3_trap"]["trap_confirmed"]).lower()
    )
    print(
        "- points pressure: "
        + report["synthetic_points_pressure"]["pressure_bucket"]
    )
    print("- flags: " + ", ".join(report["synthetic_context"]["flags"]))
    print(
        "- validation: "
        + ("OK" if guard_report["synthetic_validation_ok"] else "partial")
    )
    print(f"- report: {REPORT_PATH}")
    print(f"- guard report: {GUARD_REPORT_PATH}")


if __name__ == "__main__":
    main()
