import copy
from pathlib import Path

from final_pick_engine import load_default_final_pick_inputs
from manual_snapshot_engine import find_manual_snapshot, load_manual_snapshots
from quiniela_engine import recommend_match
from tactical_input_bridge import build_adjusted_match_inputs


LAYER_ROOT = Path(__file__).resolve().parent
SNAPSHOTS_PATH = LAYER_ROOT / "data" / "manual_match_snapshots.json"


def _probabilities(recommendation: dict) -> dict:
    team_a = recommendation["team_a"]
    team_b = recommendation["team_b"]
    probabilities = recommendation["core"]["probabilities"]
    return {
        team_a: probabilities[f"{team_a}_win"],
        "draw": probabilities["draw"],
        team_b: probabilities[f"{team_b}_win"],
    }


def _delta(base: dict, adjusted: dict) -> dict:
    return {
        key: round(adjusted[key] - base[key], 4)
        for key in base
    }


def _synthetic_players(team: str, base_rating: float) -> list[dict]:
    positions = [
        "goalkeeper",
        "defense",
        "defense",
        "defense",
        "midfield",
        "midfield",
        "midfield",
        "attack",
        "attack",
        "attack",
        "attack",
    ]
    return [
        {
            "player_name": f"{team} Synthetic {index + 1}",
            "team": team,
            "position": position,
            "overall_rating": base_rating + (index % 3),
            "source_confidence": "high",
            "evidence_level": "synthetic_test_data",
            "rating_type": "real",
        }
        for index, position in enumerate(positions)
    ]


def run_real_scenario(teams: dict) -> None:
    snapshots = load_manual_snapshots(SNAPSHOTS_PATH)
    snapshot = find_manual_snapshot(snapshots, "Netherlands", "Uzbekistan")
    recommendation = recommend_match(
        "Netherlands",
        "Uzbekistan",
        teams,
        simulations=10_000,
        seed=2026,
        simulation_mode="quick",
        match_snapshot=snapshot,
    )
    report = recommendation["adjustment_report"]
    print("Escenario real:")
    print("- partido: Netherlands vs Uzbekistan")
    print(f"- bridge status: {report['bridge_status']}")
    print(
        "- ajustes aplicados: "
        f"lineup={report['lineup_applied']} | tactica={report['tactical_applied']} | "
        f"form={report['form_applied']}"
    )
    reason = "; ".join(report["missing_data"]) if report["missing_data"] else "datos suficientes"
    print(f"- razon: {reason}")
    print("")


def run_synthetic_scenario(teams: dict) -> None:
    synthetic_teams = {
        "Bridge A": copy.deepcopy(teams["Netherlands"]),
        "Bridge B": copy.deepcopy(teams["Uzbekistan"]),
    }
    original = copy.deepcopy(synthetic_teams)
    snapshot = {
        "match": "Bridge A vs Bridge B",
        "team_a": "Bridge A",
        "team_b": "Bridge B",
        "data_status": "synthetic_test_data",
        "research_confidence": "high",
        "probable_lineups": {
            "team_a_formation": "4-3-3",
            "team_b_formation": "5-4-1",
            "data_status": "synthetic_test_data",
        },
        "formations": {
            "Bridge A": "4-3-3",
            "Bridge B": "5-4-1",
            "data_status": "synthetic_test_data",
        },
        "player_ratings": {
            "Bridge A": _synthetic_players("Bridge A", 84.0),
            "Bridge B": _synthetic_players("Bridge B", 72.0),
        },
        "form": {
            "Bridge A": 1.06,
            "Bridge B": 0.96,
        },
        "injuries_or_absences": {
            "Bridge B": [
                {
                    "player": "Bridge B Synthetic Defender",
                    "role": "defense",
                    "impact": "medium",
                    "key_player": True,
                }
            ]
        },
    }

    base = recommend_match(
        "Bridge A",
        "Bridge B",
        synthetic_teams,
        simulations=20_000,
        seed=2026,
        simulation_mode="quick",
        use_tactical_bridge=False,
    )
    adjusted = recommend_match(
        "Bridge A",
        "Bridge B",
        synthetic_teams,
        simulations=20_000,
        seed=2026,
        simulation_mode="quick",
        match_snapshot=snapshot,
        use_tactical_bridge=True,
    )
    bridge_check = build_adjusted_match_inputs("Bridge A", "Bridge B", synthetic_teams, snapshot)
    baseline_mutated = synthetic_teams != original
    base_probs = _probabilities(base)
    adjusted_probs = _probabilities(adjusted)
    deltas = _delta(base_probs, adjusted_probs)
    changed = any(abs(value) > 0 for value in deltas.values())
    report = adjusted["adjustment_report"]

    print("Escenario sintetico:")
    print(f"- bridge sin ajuste: probabilidades base {base_probs}")
    print(f"- bridge con ajuste: probabilidades ajustadas {adjusted_probs}")
    print(f"- delta probabilidades: {deltas}")
    print(f"- bridge status: {report['bridge_status']}")
    print(f"- baseline mutated: {baseline_mutated or bridge_check['adjustment_report']['baseline_mutated']}")
    print(
        "- validacion: "
        + (
            "OK si cambio cuando debia cambiar y no muto baseline"
            if changed and not baseline_mutated
            else "PENDIENTE revisar cambio de probabilidades o mutacion baseline"
        )
    )


def main() -> None:
    teams, _, _ = load_default_final_pick_inputs()
    print("NOVA TACTICAL INPUT BRIDGE DEMO")
    print("")
    run_real_scenario(teams)
    run_synthetic_scenario(teams)


if __name__ == "__main__":
    main()
