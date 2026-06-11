from __future__ import annotations

import os


def run_ai_research(
    prompt: str,
    provider: str = "manual",
    dry_run: bool = True,
) -> dict:
    provider = provider.lower().strip()
    if provider == "manual":
        return {
            "client_status": "manual_prompt_ready",
            "provider": provider,
            "dry_run": dry_run,
            "api_call_executed": False,
            "prompt": prompt,
            "message": "Copy this prompt into the research tool of choice and review output manually.",
        }
    if dry_run:
        return {
            "client_status": "dry_run_no_api_call",
            "provider": provider,
            "dry_run": True,
            "api_call_executed": False,
            "prompt": prompt,
        }
    key_name = None
    if provider == "openai":
        key_name = "OPENAI_API_KEY"
    elif provider == "anthropic":
        key_name = "ANTHROPIC_API_KEY"
    else:
        return {
            "client_status": "unsupported_provider",
            "provider": provider,
            "dry_run": dry_run,
            "api_call_executed": False,
            "message": "Only manual, openai and anthropic providers are reserved.",
        }
    if not os.environ.get(key_name):
        return {
            "client_status": "api_not_configured",
            "provider": provider,
            "dry_run": dry_run,
            "api_call_executed": False,
            "required_env_var": key_name,
            "message": "No API call executed. Configure the environment outside the repo if needed.",
        }
    return {
        "client_status": "api_execution_not_implemented",
        "provider": provider,
        "dry_run": dry_run,
        "api_call_executed": False,
        "required_env_var": key_name,
        "message": "Real API execution is intentionally pending explicit implementation.",
    }
