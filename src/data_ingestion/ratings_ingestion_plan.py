"""
Ratings ingestion plan.

Next real integrations:
1. FIFA ranking complete table.
2. World Football Elo complete table.
3. xG provider.
4. player/squad provider.
5. injury provider.

This file is intentionally a plan/scaffold to avoid pretending that missing data is already integrated.
"""

REQUIRED_FIELDS = [
    "team",
    "fifa_rank",
    "fifa_points",
    "world_football_elo",
    "xg_for",
    "xg_against",
    "last_10_form",
    "squad_strength",
    "injury_adjustment",
    "tactical_profile",
]