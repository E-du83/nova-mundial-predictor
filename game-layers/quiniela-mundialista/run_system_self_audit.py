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
    print("World Cup 2026 Fixture")
    print(f"- fixture type: {audit['readiness']['worldcup_2026_fixture_type']}")
    print(f"- validation: {audit['readiness']['worldcup_2026_fixture_validation']}")
    print(f"- importer existe: {'si' if audit['readiness']['worldcup_2026_fixture_importer_exists'] else 'no'}")
    print(f"- guard existe: {'si' if audit['readiness']['worldcup_2026_fixture_guard_exists'] else 'no'}")
    print(f"- guard status: {audit['readiness']['worldcup_2026_guard_status']}")
    print(
        "- bloquea picks con placeholder: "
        f"{'si' if audit['readiness']['worldcup_2026_blocks_placeholder_picks'] else 'no'}"
    )
    print(
        "- protegido contra fixture no verificado: "
        f"{'si' if audit['readiness']['worldcup_2026_protected_against_unverified_fixture'] else 'no'}"
    )
    print(
        "- snapshot oficial cargado: "
        f"{'si' if audit['readiness']['worldcup_2026_official_snapshot_loaded'] else 'no'}"
    )
    print(f"- estructura lista: {'si' if audit['readiness']['worldcup_2026_structure_ready'] else 'no'}")
    print(f"- placeholder fixture: {'si' if audit['readiness']['worldcup_2026_fixture_is_placeholder'] else 'no'}")
    print(f"- faltan grupos reales: {'si' if audit['readiness']['worldcup_2026_missing_real_groups'] else 'no'}")
    print(f"- faltan horarios UTC reales: {'si' if audit['readiness']['worldcup_2026_missing_kickoff_utc'] else 'no'}")
    print(f"- faltan sedes reales: {'si' if audit['readiness']['worldcup_2026_missing_real_venues'] else 'no'}")
    print(f"- groups loaded: {audit['readiness']['worldcup_2026_groups_loaded']}")
    print(f"- slots loaded: {audit['readiness']['worldcup_2026_slots_loaded']}")
    print(f"- confirmed matches: {audit['readiness']['worldcup_2026_confirmed_matches']}")
    print(f"- pending matches: {audit['readiness']['worldcup_2026_pending_matches']}")
    print(
        "- puede correr simulacion completa: "
        f"{'si' if audit['readiness']['worldcup_2026_ready_for_full_group_simulation'] else 'no'}"
    )
    print("World Cup 2022 Blind Test")
    print(f"- existe: {'si' if audit['readiness']['worldcup_2022_blind_test_exists'] else 'no'}")
    print(f"- leakage guard: {audit['readiness']['worldcup_2022_leakage_guard_status']}")
    print(f"- usa baseline 2026: {'si' if audit['readiness']['worldcup_2022_uses_2026_baseline'] else 'no'}")
    print(f"- perfiles historicos faltantes: {audit['readiness']['worldcup_2022_missing_historical_profiles']}")
    print(f"- perfiles con defaults neutrales: {audit['readiness']['worldcup_2022_neutral_defaults_only']}")
    print(f"- partidos evaluados: {audit['readiness']['worldcup_2022_matches_evaluated']}")
    print(
        "- partidos evaluados con defaults neutrales: "
        f"{audit['readiness']['worldcup_2022_matches_evaluable_with_neutral_defaults']}"
    )
    print(
        "- muestra Quinigol insuficiente: "
        f"{'si' if audit['readiness']['quinigol_timing_sample_insufficient'] else 'no'}"
    )
    print(f"- puede recalibrar: {'si' if audit['readiness']['worldcup_2022_can_recalibrate'] else 'no'}")


if __name__ == "__main__":
    main()
