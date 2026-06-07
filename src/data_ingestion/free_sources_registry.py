"""
Registry of free or optional football data sources.

The registry is descriptive. It does not call the internet and does not make any
paid source mandatory for the project.
"""


FREE_SOURCES = [
    {
        "source_id": "fifa_official",
        "name": "FIFA official",
        "type": "official_site",
        "cost": "free_public_reference",
        "requires_api_key": False,
        "reliability": "alta",
        "intended_use": [
            "calendario",
            "sedes",
            "grupos",
            "fixtures",
            "fase",
            "horarios",
        ],
        "limitations": [
            "Puede requerir captura manual o endpoint no documentado.",
            "No se debe hacer scraping agresivo.",
        ],
        "url_reference_text": "https://www.fifa.com/",
        "status": "official",
    },
    {
        "source_id": "openfootball_worldcup",
        "name": "openfootball/worldcup.json",
        "type": "open_data_repo",
        "cost": "free",
        "requires_api_key": False,
        "reliability": "media_alta",
        "intended_use": [
            "datos open source de World Cup en JSON",
            "fixtures",
            "grupos",
        ],
        "limitations": [
            "Depende de actualizacion del repositorio.",
            "Verificar licencia en el repo antes de redistribuir snapshots.",
        ],
        "url_reference_text": "https://github.com/openfootball/worldcup.json",
        "status": "open_data",
    },
    {
        "source_id": "world_football_elo",
        "name": "World Football Elo Ratings",
        "type": "open_web_data",
        "cost": "free",
        "requires_api_key": False,
        "reliability": "alta",
        "intended_use": [
            "rating de selecciones",
            "fuerza relativa",
        ],
        "limitations": [
            "Necesita snapshot verificado para no depender de scraping.",
            "Puede cambiar con nuevos partidos.",
        ],
        "url_reference_text": "https://www.eloratings.net/",
        "status": "open_web_data",
    },
    {
        "source_id": "jgravier_soccer_elo",
        "name": "JGravier/soccer-elo",
        "type": "open_source_repo",
        "cost": "free",
        "requires_api_key": False,
        "reliability": "media",
        "intended_use": [
            "historico Elo",
            "backtesting",
        ],
        "limitations": [
            "Puede no estar actualizado a 2026 final.",
            "Requiere validacion contra fuente Elo actual.",
        ],
        "url_reference_text": "https://github.com/JGravier/soccer-elo",
        "status": "open_source_repo",
    },
    {
        "source_id": "open_meteo",
        "name": "Open-Meteo",
        "type": "free_api",
        "cost": "free",
        "requires_api_key": False,
        "reliability": "alta",
        "intended_use": [
            "clima historico por sede",
            "temperatura",
            "humedad",
            "clima promedio",
        ],
        "limitations": [
            "Requiere latitud, longitud y rango de fechas.",
            "No sustituye reporte meteorologico oficial del dia.",
        ],
        "url_reference_text": "https://open-meteo.com/",
        "status": "free_api",
    },
    {
        "source_id": "the_odds_api",
        "name": "The Odds API",
        "type": "optional_limited_api",
        "cost": "free_limited_or_paid",
        "requires_api_key": True,
        "reliability": "media_alta",
        "intended_use": [
            "cuotas",
            "movimiento de mercado si el plan lo permite",
        ],
        "limitations": [
            "No usar como dependencia obligatoria si requiere pago.",
            "Tiene limites de plan y requiere API key.",
        ],
        "url_reference_text": "https://the-odds-api.com/",
        "status": "optional_limited_api",
    },
    {
        "source_id": "awesome_football_data",
        "name": "GitHub football datasets / awesome football data",
        "type": "reference_registry",
        "cost": "free",
        "requires_api_key": False,
        "reliability": "variable",
        "intended_use": [
            "descubrimiento de datasets",
            "referencias open source",
        ],
        "limitations": [
            "No todos los datasets estan actualizados.",
            "Cada fuente debe validarse por licencia y calidad.",
        ],
        "url_reference_text": "https://github.com/topics/football-data",
        "status": "reference_registry",
    },
]


def get_sources() -> list[dict]:
    return list(FREE_SOURCES)


def get_free_sources() -> list[dict]:
    return [
        source
        for source in FREE_SOURCES
        if source["cost"] in ("free", "free_public_reference")
        and not source["requires_api_key"]
    ]


def get_sources_requiring_api_key() -> list[dict]:
    return [source for source in FREE_SOURCES if source["requires_api_key"]]


def get_source_by_id(source_id: str) -> dict | None:
    for source in FREE_SOURCES:
        if source["source_id"] == source_id:
            return source
    return None
