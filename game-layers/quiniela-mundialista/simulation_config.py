SIMULATION_MODES = {
    "quick": 10_000,
    "standard": 100_000,
    "final": 1_000_000,
}


def resolve_simulation_mode(mode: str = "quick") -> tuple[str, int]:
    normalized = mode.strip().lower()
    if normalized not in SIMULATION_MODES:
        raise ValueError("Modo de simulacion invalido. Usar: quick, standard o final.")
    return normalized, SIMULATION_MODES[normalized]


def infer_simulation_mode(simulations: int) -> str:
    for mode, value in SIMULATION_MODES.items():
        if simulations == value:
            return mode
    return "custom"
