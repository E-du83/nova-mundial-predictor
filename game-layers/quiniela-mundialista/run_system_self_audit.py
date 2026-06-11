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
    print("Full Group Stage Picks Runner")
    print(f"- runner existe: {'si' if audit['readiness']['full_group_stage_runner_exists'] else 'no'}")
    print(f"- CLI existe: {'si' if audit['readiness']['full_group_stage_cli_exists'] else 'no'}")
    print(f"- runner status: {audit['readiness']['full_group_stage_runner_status']}")
    print(f"- respeta fixture guard: {'si' if audit['readiness']['full_group_stage_runner_respects_guard'] else 'no'}")
    print(
        "- genera picks con placeholder: "
        f"{'si' if audit['readiness']['full_group_stage_runner_generates_placeholder_picks'] else 'no'}"
    )
    print(
        "- actualiza prediction_history con placeholder: "
        f"{'si' if audit['readiness']['full_group_stage_prediction_history_updated'] else 'no'}"
    )
    print(
        "- operativamente bloqueado: "
        f"{'si' if audit['readiness']['full_group_stage_operationally_blocked'] else 'no'}"
    )
    print("Group Context Engine")
    print(f"- engine existe: {'si' if audit['readiness']['group_context_engine_exists'] else 'no'}")
    print(f"- demo existe: {'si' if audit['readiness']['group_context_demo_exists'] else 'no'}")
    print(f"- rules existen: {'si' if audit['readiness']['group_context_rules_exists'] else 'no'}")
    print(f"- estado real: {audit['readiness']['group_context_real_status']}")
    print(
        "- se activa con placeholder: "
        f"{'si' if audit['readiness']['group_context_activates_with_placeholder'] else 'no'}"
    )
    print(
        "- no usa resultados futuros: "
        f"{'si' if audit['readiness']['group_context_no_future_results'] else 'no'}"
    )
    print(
        "- jornada 3 requiere tabla previa: "
        f"{'si' if audit['readiness']['group_context_jornada3_requires_standings'] else 'no'}"
    )
    print(
        "- falta fixture oficial para contexto real: "
        f"{'si' if audit['readiness']['group_context_needs_official_fixture'] else 'no'}"
    )
    print("World Cup 2026 Official Bracket")
    print(f"- bracket scaffold existe: {'si' if audit['readiness']['bracket_scaffold_exists'] else 'no'}")
    print(f"- bracket guard existe: {'si' if audit['readiness']['bracket_guard_exists'] else 'no'}")
    print(f"- third-place selector existe: {'si' if audit['readiness']['third_place_selector_exists'] else 'no'}")
    print(f"- third-place rules existen: {'si' if audit['readiness']['third_place_rules_exists'] else 'no'}")
    print(f"- bracket guard status: {audit['readiness']['bracket_guard_status']}")
    print(
        "- construye bracket real sin grupos cerrados: "
        f"{'si' if audit['readiness']['bracket_builds_real_without_group_results'] else 'no'}"
    )
    print(
        "- inventa mejores terceros: "
        f"{'si' if audit['readiness']['bracket_invents_best_thirds'] else 'no'}"
    )
    print(
        "- matriz terceros pendiente snapshot oficial: "
        f"{'si' if audit['readiness']['third_place_matrix_pending'] else 'no'}"
    )
    print(f"- knockout picks bloqueados: {'si' if audit['readiness']['knockout_picks_blocked'] else 'no'}")
    print("Research Automation")
    print(f"- existe: {'si' if audit['readiness']['research_automation_exists'] else 'no'}")
    print(f"- sin API keys hardcoded: {'si' if audit['readiness']['research_no_api_keys_hardcoded'] else 'no'}")
    print(f"- dry-run por defecto: {'si' if audit['readiness']['research_dry_run_default'] else 'no'}")
    print(f"- API calls enabled: {'si' if audit['readiness']['research_api_calls_enabled'] else 'no'}")
    print(f"- no muta baseline: {'si' if audit['readiness']['research_no_baseline_mutation'] else 'no'}")
    print(f"- no auto-merge: {'si' if audit['readiness']['research_no_auto_merge'] else 'no'}")
    print(f"- requiere revision manual: {'si' if audit['readiness']['research_requires_manual_review'] else 'no'}")
    print(
        "- snapshots directory existe: "
        f"{'si' if audit['readiness']['research_snapshots_directory_exists'] else 'no'}"
    )
    print("Inter Phase Updater")
    print(f"- updater existe: {'si' if audit['readiness']['inter_phase_updater_exists'] else 'no'}")
    print(f"- freeze engine existe: {'si' if audit['readiness']['phase_freeze_engine_exists'] else 'no'}")
    print(f"- results loader existe: {'si' if audit['readiness']['results_loader_exists'] else 'no'}")
    print(f"- standings engine existe: {'si' if audit['readiness']['standings_engine_exists'] else 'no'}")
    print(f"- transition guard existe: {'si' if audit['readiness']['phase_transition_guard_exists'] else 'no'}")
    print(f"- update status: {audit['readiness']['inter_phase_update_status']}")
    print(
        "- dry-run no modifica historial: "
        f"{'si' if audit['readiness']['inter_phase_dry_run_no_history_mutation'] else 'no'}"
    )
    print(
        "- recalibracion aplicada: "
        f"{'si' if audit['readiness']['inter_phase_recalibration_applied'] else 'no'}"
    )
    print(
        "- avanza sin resultados: "
        f"{'si' if audit['readiness']['inter_phase_advances_without_results'] else 'no'}"
    )
    print(
        "- construye bracket sin standings: "
        f"{'si' if audit['readiness']['inter_phase_builds_bracket_without_standings'] else 'no'}"
    )
    print(
        "- falta fixture oficial/resultados: "
        f"{'si' if audit['readiness']['inter_phase_missing_fixture_or_results'] else 'no'}"
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
