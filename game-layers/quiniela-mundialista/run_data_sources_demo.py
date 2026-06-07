from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from data_ingestion.data_source_validator import summarize_sources  # noqa: E402
from data_ingestion.free_sources_registry import (  # noqa: E402
    get_free_sources,
    get_sources,
    get_sources_requiring_api_key,
)
from data_ingestion.open_meteo_client import offline_profile_scaffold  # noqa: E402
from data_ingestion.openfootball_client import connection_notes  # noqa: E402
from data_ingestion.world_elo_client import manual_snapshot_requirements  # noqa: E402


def _print_source(source: dict) -> None:
    print(f"- {source['source_id']}: {source['name']}")
    print(f"  tipo: {source['type']}")
    print(f"  costo: {source['cost']}")
    print(f"  api key: {source['requires_api_key']}")
    print(f"  estado: {source['status']}")
    print(f"  confiabilidad: {source['reliability']}")
    print(f"  uso: {', '.join(source['intended_use'])}")


def main() -> None:
    sources = get_sources()
    summary = summarize_sources(sources)

    print("NOVA DATA SOURCES DEMO - OPEN SOURCE + FRIENDLY TEST")
    print("")
    print("FUENTES REGISTRADAS")
    for source in sources:
        _print_source(source)
    print("")

    print("FUENTES GRATIS SIN API KEY")
    for source in get_free_sources():
        print(f"- {source['source_id']}: {source['name']}")
    print("")

    print("FUENTES QUE REQUIEREN API KEY")
    for source in get_sources_requiring_api_key():
        print(f"- {source['source_id']}: {source['name']}")
    print("")

    print("LISTAS / PENDIENTES")
    print(f"Listas: {', '.join(summary['ready_sources'])}")
    print(f"Pendientes o a validar: {', '.join(summary['pending_sources'])}")
    print("")

    print("SCAFFOLDS OFFLINE")
    print(f"openfootball: {connection_notes()['mode']}")
    print(
        "world_elo required fields: "
        f"{', '.join(manual_snapshot_requirements()['required_fields'])}"
    )
    print(
        "open_meteo status: "
        f"{offline_profile_scaffold('pending_real_venue')['status']}"
    )
    print("")

    print("PROXIMOS DATOS A LLENAR")
    print("- snapshot local openfootball si aplica")
    print("- CSV manual verificado de World Football Elo")
    print("- sedes y coordenadas para Open-Meteo")
    print("- cuotas manuales si el usuario aporta snapshot visible")


if __name__ == "__main__":
    main()
