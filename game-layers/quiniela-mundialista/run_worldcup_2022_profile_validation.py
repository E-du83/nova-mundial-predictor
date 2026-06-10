from worldcup_2022_profile_builder import build_2022_prematch_profiles
from worldcup_2022_profile_validator import validate_2022_profiles
from worldcup_2022_dataset_loader import PROFILE_AUDIT_PATH, PROFILES_PATH


def main() -> None:
    build = build_2022_prematch_profiles()
    audit = validate_2022_profiles()

    print("NOVA WORLD CUP 2022 PROFILE VALIDATION")
    print(f"- teams found: {build['teams_found']}")
    print(f"- profiles created: {build['profiles_created']}")
    print(f"- profiles verified: {audit['profiles_verified']}")
    print(f"- profiles pending verification: {audit['profiles_pending_verification']}")
    print(f"- neutral defaults used: {audit['profiles_using_neutral_defaults']}")
    print(f"- blocked profiles: {audit['profiles_blocked']}")
    print(f"- audit status: {audit['audit_status']}")
    print("Warnings:")
    for warning in build["warnings"] + audit["source_warnings"] + audit["cutoff_warnings"] + audit["leakage_warnings"]:
        print(f"- {warning}")
    print("Output paths:")
    print(f"- profiles: {PROFILES_PATH}")
    print(f"- audit: {PROFILE_AUDIT_PATH}")


if __name__ == "__main__":
    main()
