from __future__ import annotations

from research_prompt_builder import build_research_prompt


def main() -> None:
    match = "Netherlands vs Uzbekistan"
    prompt = build_research_prompt(
        match=match,
        team_a="Netherlands",
        team_b="Uzbekistan",
        kickoff_utc="pending_verification",
        competition="International Friendly",
    )
    print("NOVA RESEARCH PROMPT BUILDER DEMO")
    print(f"- match: {match}")
    print("- output esperado: JSON compatible con research_snapshot_schema")
    print("- nota: no API call executed")
    print("")
    print(prompt)


if __name__ == "__main__":
    main()
