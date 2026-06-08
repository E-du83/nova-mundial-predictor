from system_self_audit import build_system_self_audit


def _print_section(title: str, items: list[str]) -> None:
    print(title)
    for item in items:
        print(f"- {item}")
    print("")


def main() -> None:
    audit = build_system_self_audit()
    print("NOVA SYSTEM SELF AUDIT")
    _print_section("Fortalezas", audit["fortalezas"])
    _print_section("Debilidades", audit["debilidades"])
    _print_section("Riesgos", audit["riesgos"])
    _print_section("Mejoras prioritarias", audit["mejoras_prioritarias"])
    _print_section("Mejoras opcionales", audit["mejoras_opcionales"])
    _print_section("No hacer todavia", audit["no_hacer_todavia"])
    print(f"Siguiente bloque recomendado: {audit['siguiente_bloque_recomendado']}")
    print(f"Listo para quiniela completa: {'si' if audit['readiness']['ready_for_full_quiniela'] else 'no'}")
    print(f"Listo para venta: {'si' if audit['readiness']['ready_for_sale'] else 'no'}")


if __name__ == "__main__":
    main()
