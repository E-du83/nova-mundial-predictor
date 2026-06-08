"""
Open-Meteo historical weather scaffold.

This module builds request parameters/URLs only. It does not call the internet
by default, so demos can run offline.
"""

from urllib.parse import urlencode


ARCHIVE_ENDPOINT = "https://archive-api.open-meteo.com/v1/archive"
SOURCE_METADATA = {
    "source": "open_meteo",
    "source_id": "open_meteo",
    "cost": "free",
    "requires_api_key": False,
}
DEFAULT_DAILY_VARIABLES = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "relative_humidity_2m_mean",
]


def build_historical_weather_params(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    daily: list[str] | None = None,
    timezone: str = "auto",
) -> dict:
    return {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(daily or DEFAULT_DAILY_VARIABLES),
        "timezone": timezone,
    }


def build_historical_weather_url(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    daily: list[str] | None = None,
    timezone: str = "auto",
) -> str:
    params = build_historical_weather_params(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        daily=daily,
        timezone=timezone,
    )
    return f"{ARCHIVE_ENDPOINT}?{urlencode(params)}"


def build_historical_weather_request(
    venue: str,
    latitude: float | None,
    longitude: float | None,
    start_date: str,
    end_date: str,
    daily: list[str] | None = None,
    timezone: str = "auto",
) -> dict:
    if latitude is None or longitude is None:
        return {
            **SOURCE_METADATA,
            "venue": venue,
            "latitude": latitude if latitude is not None else "pending_real_data",
            "longitude": longitude if longitude is not None else "pending_real_data",
            "start_date": start_date,
            "end_date": end_date,
            "data_status": "pending_coordinates",
            "url": "pending_coordinates",
            "mode": "offline_scaffold",
        }

    return {
        **SOURCE_METADATA,
        "venue": venue,
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "data_status": "ready_url",
        "url": build_historical_weather_url(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            daily=daily,
            timezone=timezone,
        ),
        "mode": "offline_url_builder",
        "network_policy": "caller_may_fetch_later; this function does not require internet",
    }


def offline_profile_scaffold(venue: str, latitude: float | None = None, longitude: float | None = None) -> dict:
    data_status = "ready_url" if latitude is not None and longitude is not None else "pending_coordinates"
    return {
        **SOURCE_METADATA,
        "source_id": "open_meteo",
        "mode": "scaffold_offline",
        "venue": venue,
        "latitude": latitude if latitude is not None else "pending_real_data",
        "longitude": longitude if longitude is not None else "pending_real_data",
        "required_for_request": [
            "latitude",
            "longitude",
            "start_date",
            "end_date",
        ],
        "status": data_status,
        "data_status": data_status,
        "message": "Fill coordinates and date range before making an Open-Meteo request.",
    }
