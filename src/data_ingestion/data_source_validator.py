"""
Small validators for data source readiness.
"""

import json
from pathlib import Path


PENDING_STATUSES = {
    "pending_real_data",
    "pending_manual_snapshot",
    "manual_snapshot_required",
    "not_available_free",
    "pre_tournament_context",
}


def validate_file_exists(path: str | Path) -> dict:
    file_path = Path(path)
    return {
        "path": str(file_path),
        "exists": file_path.exists(),
        "status": "available" if file_path.exists() else "pending_manual_snapshot",
    }


def validate_json_fields(path: str | Path, required_fields: list[str]) -> dict:
    file_path = Path(path)
    existence = validate_file_exists(file_path)
    if not existence["exists"]:
        return {
            **existence,
            "usable": False,
            "missing_fields": required_fields,
        }

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "path": str(file_path),
            "exists": True,
            "usable": False,
            "status": "invalid_json",
            "message": str(exc),
        }

    missing_fields = [field for field in required_fields if field not in data]
    return {
        "path": str(file_path),
        "exists": True,
        "usable": not missing_fields,
        "status": "available" if not missing_fields else "missing_required_fields",
        "missing_fields": missing_fields,
    }


def validate_source_entry(source: dict) -> dict:
    required = [
        "source_id",
        "name",
        "type",
        "cost",
        "requires_api_key",
        "reliability",
        "intended_use",
        "limitations",
        "url_reference_text",
        "status",
    ]
    missing = [field for field in required if field not in source]
    status = source.get("status", "missing_source_status")
    needs_api_key = bool(source.get("requires_api_key"))
    is_reference_only = status == "reference_registry"
    is_pending = status in PENDING_STATUSES or needs_api_key or is_reference_only
    return {
        "source_id": source.get("source_id", "missing_source_id"),
        "usable": not missing and not is_pending,
        "status": status,
        "missing_fields": missing,
        "is_pending": is_pending,
    }


def summarize_sources(sources: list[dict]) -> dict:
    validations = [validate_source_entry(source) for source in sources]
    return {
        "total_sources": len(sources),
        "ready_sources": [
            item["source_id"]
            for item in validations
            if item["usable"]
        ],
        "pending_sources": [
            item["source_id"]
            for item in validations
            if item["is_pending"] or not item["usable"]
        ],
        "validations": validations,
    }
