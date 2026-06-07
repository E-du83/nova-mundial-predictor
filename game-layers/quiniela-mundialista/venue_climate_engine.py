import json
from pathlib import Path


PENDING_VALUE = "pending_real_data"


def load_venue_climate_profiles(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _pending_profile(venue: str = "pending_real_venue") -> dict:
    return {
        "venue": venue,
        "city": PENDING_VALUE,
        "country": PENDING_VALUE,
        "month": PENDING_VALUE,
        "avg_temp_c": PENDING_VALUE,
        "avg_humidity": PENDING_VALUE,
        "altitude_m": PENDING_VALUE,
        "heat_risk": PENDING_VALUE,
        "adaptation_risk": PENDING_VALUE,
        "source": PENDING_VALUE,
        "data_status": PENDING_VALUE,
    }


def build_venue_climate_profile(
    venue: str,
    profiles_data: dict | None = None,
) -> dict:
    if not venue:
        venue = "pending_real_venue"

    for profile in (profiles_data or {}).get("profiles", []):
        if profile.get("venue", "").strip().lower() == venue.strip().lower():
            return {
                "venue": profile.get("venue", venue),
                "city": profile.get("city", PENDING_VALUE),
                "country": profile.get("country", PENDING_VALUE),
                "month": profile.get("month", PENDING_VALUE),
                "avg_temp_c": profile.get("avg_temp_c", PENDING_VALUE),
                "avg_humidity": profile.get("avg_humidity", PENDING_VALUE),
                "altitude_m": profile.get("altitude_m", PENDING_VALUE),
                "heat_risk": profile.get("heat_risk", PENDING_VALUE),
                "adaptation_risk": profile.get("adaptation_risk", PENDING_VALUE),
                "source": profile.get("source", PENDING_VALUE),
                "data_status": profile.get("data_status", PENDING_VALUE),
            }

    return _pending_profile(venue)


def climate_missing_data(profile: dict) -> list[str]:
    missing = []
    for key in (
        "city",
        "country",
        "month",
        "avg_temp_c",
        "avg_humidity",
        "altitude_m",
        "heat_risk",
        "adaptation_risk",
    ):
        if profile.get(key) == PENDING_VALUE:
            missing.append(key)
    return missing
