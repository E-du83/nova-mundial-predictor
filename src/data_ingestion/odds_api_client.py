"""
Odds API client scaffold.

This file is intentionally safe:
- It does not include API keys.
- It does not call paid services unless configured.
- It explains exactly what is needed.

Recommended env var:
THE_ODDS_API_KEY
"""

import os
import json
from urllib.parse import urlencode
from urllib.request import urlopen


class OddsApiNotConfiguredError(Exception):
    pass


def get_api_key():
    key = os.getenv("THE_ODDS_API_KEY")
    if not key:
        raise OddsApiNotConfiguredError(
            "Missing THE_ODDS_API_KEY. Create an API key and set it as an environment variable."
        )
    return key


def build_odds_api_url(sport_key="soccer_fifa_world_cup", regions="us,uk,eu", markets="h2h", odds_format="decimal"):
    key = get_api_key()
    params = urlencode({
        "apiKey": key,
        "regions": regions,
        "markets": markets,
        "oddsFormat": odds_format,
    })
    return f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?{params}"


def fetch_odds_from_api():
    url = build_odds_api_url()
    with urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    print("This is a scaffold. Set THE_ODDS_API_KEY before running.")