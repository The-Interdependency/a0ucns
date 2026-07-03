# ratios: loc_comments=76:0 imports_exports=2:2 calls_definitions=15:2
from __future__ import annotations

from typing import Any, Dict, List


def get_ai_instruction_payload() -> Dict[str, Any]:
    return {
        "hub_name": "AIMMH Hub",
        "goal": "Run multi-model prompt workflows, compare outputs, and synthesize decisions.",
        "quickstart": [
            "Open Registry and verify model availability.",
            "Instantiate at least 2 model instances.",
            "Choose one mode: direct chat or staged run pipeline.",
            "Compare responses in stack/pane modes.",
            "Queue selected blocks and run synthesis.",
        ],
        "patterns": [
            {
                "pattern": "fan_out",
                "best_for": "parallel brainstorming and broad option generation",
            },
            {
                "pattern": "daisy_chain",
                "best_for": "sequential refinement and stepwise transformation",
            },
            {
                "pattern": "room_all",
                "best_for": "group-wide discussion where every participant contributes",
            },
            {
                "pattern": "room_synthesized",
                "best_for": "discussion followed by single synthesis output",
            },
            {
                "pattern": "council",
                "best_for": "debate, critique, and consensus recommendations",
            },
            {
                "pattern": "roleplay",
                "best_for": "simulations with DM + player participant structure",
            },
        ],
        "operating_notes": [
            "Prefer 2-5 focused instances per task for reliable comparison.",
            "Use short explicit stage prompts for better consistency.",
            "For synthesis, include only high-signal response blocks.",
            "Use compare popout when reviewing 2+ candidate responses side-by-side.",
        ],
        "api_endpoints": {
            "health": "/api/health",
            "ready": "/api/ready",
            "hub_base": "/api/v1/hub",
            "registry": "/api/v1/registry",
        },
    }


def get_ai_instruction_text() -> str:
    payload = get_ai_instruction_payload()
    lines: List[str] = [
        "AIMMH Hub — AI Visitor Guide",
        "",
        f"Goal: {payload['goal']}",
        "",
        "Quickstart:",
    ]
    lines.extend([f"- {step}" for step in payload["quickstart"]])
    lines.append("")
    lines.append("Patterns:")
    for item in payload["patterns"]:
        lines.append(f"- {item['pattern']}: {item['best_for']}")
    lines.append("")
    lines.append("Operating Notes:")
    lines.extend([f"- {note}" for note in payload["operating_notes"]])
    lines.append("")
    lines.append("System Endpoints:")
    lines.append(f"- Health: {payload['api_endpoints']['health']}")
    lines.append(f"- Ready: {payload['api_endpoints']['ready']}")
    lines.append(f"- Hub API: {payload['api_endpoints']['hub_base']}")
    lines.append(f"- Registry API: {payload['api_endpoints']['registry']}")
    return "\n".join(lines)
# ratios: loc_comments=76:0 imports_exports=2:2 calls_definitions=15:2
