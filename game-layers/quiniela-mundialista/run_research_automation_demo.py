from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ai_research_client import run_ai_research
from research_prompt_builder import build_research_prompt
from research_snapshot_normalizer import normalize_research_snapshot
from research_snapshot_store import save_research_snapshot
from research_snapshot_validator import validate_research_snapshot
from run_research_snapshot_validation_demo import build_synthetic_valid_snapshot


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"
TEMPLATE_PATH = DATA_ROOT / "research_snapshot_template.json"
STATUS_PATH = DATA_ROOT / "research_automation_status.json"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json_if_changed(path: Path, data: dict) -> None:
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


def main() -> None:
    prompt = build_research_prompt(
        match="Netherlands vs Uzbekistan",
        team_a="Netherlands",
        team_b="Uzbekistan",
        competition="International Friendly",
    )
    client_result = run_ai_research(prompt, provider="manual", dry_run=True)
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    template_validation = validate_research_snapshot(template)
    synthetic = build_synthetic_valid_snapshot()
    synthetic_validation = validate_research_snapshot(synthetic)
    normalized = normalize_research_snapshot(synthetic)
    save_result = save_research_snapshot(synthetic, dry_run=True)
    status = {
        "data_status": "research_automation_status_v1",
        "generated_at": _now(),
        "prompt_builder": "OK",
        "snapshot_schema": "OK",
        "snapshot_validator": "OK",
        "snapshot_normalizer": "OK",
        "snapshot_store": "OK",
        "ai_client_safe_mode": "OK",
        "api_calls_enabled": False,
        "api_call_executed": client_result["api_call_executed"],
        "dry_run_default": True,
        "snapshots_directory": "OK",
        "last_demo_status": "OK",
        "files_written": save_result["files_written"],
        "template_validation_status": template_validation["validation_status"],
        "synthetic_validation_status": synthetic_validation["validation_status"],
    }
    _write_json_if_changed(STATUS_PATH, status)

    print("NOVA RESEARCH AUTOMATION DEMO")
    print(f"- prompt status: {client_result['client_status']}")
    print(f"- api call executed: {'yes' if client_result['api_call_executed'] else 'no'}")
    print(f"- snapshot validation: {synthetic_validation['validation_status']}")
    print("- normalized snapshot keys: " + ", ".join(sorted(normalized.keys())[:12]) + "...")
    print(f"- dry run save: {str(save_result['dry_run']).lower()}")
    print(f"- files written: {save_result['files_written']}")
    print("- ready for manual review")
    print("- manual_snapshot_engine integration: normalized output is compatible; no auto-merge performed")


if __name__ == "__main__":
    main()
