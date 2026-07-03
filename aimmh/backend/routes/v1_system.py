# ratios: loc_comments=70:3 imports_exports=3:5 calls_definitions=13:5
"""V1 System endpoints — health, version, PTCA schema."""

from fastapi import APIRouter
from services.llm import DEFAULT_REGISTRY
from services.ai_instructions import get_ai_instruction_payload

router = APIRouter(prefix="/api/v1", tags=["system"])

BUILD_VERSION = "v1.0.2-S9"


@router.get("/health")
async def health():
    return {"status": "ok", "build": BUILD_VERSION}


@router.get("/version")
async def version():
    return {
        "version": BUILD_VERSION,
        "spec": "spec.md v1.0.2-S9",
        "components": ["EDCM", "PTCA", "PCNA"],
    }


@router.get("/ptca/schema")
async def ptca_schema():
    """Return the canonical PTCA tensor schema (frozen v1.0.2)."""
    return {
        "tensor": {
            "name": "ptca_core",
            "axes": [
                {"label": "prime_node", "size": 53, "meaning": "prime-indexed routing nodes"},
                {"label": "sentinel", "size": 9, "meaning": "S1..S9 control channels"},
                {"label": "phase", "size": 8, "meaning": "phase cycle"},
                {"label": "hept", "size": 7, "meaning": "heptagram association slot (6 ring + 1 hub)"},
            ],
            "indexing": {"prime_node": "first_53_primes"},
            "sentinel_index": {
                "0": "S1_PROVENANCE",
                "1": "S2_POLICY",
                "2": "S3_BOUNDS",
                "3": "S4_APPROVAL",
                "4": "S5_CONTEXT",
                "5": "S6_IDENTITY",
                "6": "S7_MEMORY",
                "7": "S8_RISK",
                "8": "S9_AUDIT",
            },
        },
        "exchange_constants": {
            "delta": 1,
            "alpha": 0.10,
            "beta": 0.20,
            "gamma": 0.10,
            "agg6": "mean",
            "agg_seeds": "mean",
        },
        "seed_count": 53,
        "version": BUILD_VERSION,
    }


@router.get("/models")
async def list_available_models():
    """List all available model developers and their models."""
    result = []
    for dev_id, dev in DEFAULT_REGISTRY.items():
        models = []
        for m in dev.get("models", []):
            if isinstance(m, dict):
                models.append({"model_id": m["model_id"], "display_name": m.get("display_name", m["model_id"])})
            else:
                models.append({"model_id": m, "display_name": m})
        result.append({
            "developer_id": dev_id,
            "name": dev["name"],
            "auth_type": dev["auth_type"],
            "models": models,
        })
    return {"developers": result}


@router.get("/ai-instructions")
async def ai_instructions_v1():
    return get_ai_instruction_payload()
# ratios: loc_comments=70:3 imports_exports=3:5 calls_definitions=13:5
