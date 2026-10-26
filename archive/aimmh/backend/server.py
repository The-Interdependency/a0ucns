# ratios: loc_comments=99:3 imports_exports=23:7 calls_definitions=37:8
from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, PlainTextResponse
import os
import logging
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from db import client
from routes.auth import router as auth_router
from routes.agent_zero import router as agent_zero_router
from routes.v1_a0 import router as v1_a0_router
from routes.v1_edcm import router as v1_edcm_router
from routes.v1_system import router as v1_system_router
from routes.registry import router as registry_router
from routes.keys import router as keys_router
from routes.v1_analysis import router as analysis_router
from routes.v1_lib import router as v1_lib_router
from routes.v1_hub import router as v1_hub_router
from routes.v1_hub_state import router as v1_hub_state_router
from routes.payments_v2 import router as payments_router
from routes.console import router as console_router
from services.ai_instructions import get_ai_instruction_payload, get_ai_instruction_text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="Multi-Model Hub", version="1.0.2-S9")
app.state.startup_time = datetime.now(timezone.utc).isoformat()


async def _check_mongo_ready() -> tuple[bool, str]:
    try:
        await client.admin.command("ping")
        return True, "ok"
    except Exception as exc:
        return False, str(exc)

# Auth (kept from existing)
app.include_router(auth_router)

# Agent Zero endpoints
app.include_router(agent_zero_router)

# V1 API surface
app.include_router(v1_a0_router)
app.include_router(v1_edcm_router)
app.include_router(v1_system_router)
app.include_router(registry_router)
app.include_router(keys_router)
app.include_router(analysis_router)
app.include_router(v1_lib_router)
app.include_router(v1_hub_router)
app.include_router(v1_hub_state_router)
app.include_router(payments_router)
app.include_router(console_router)

cors_origins_raw = os.environ.get('CORS_ORIGINS')
if not cors_origins_raw:
    raise RuntimeError('CORS_ORIGINS is required')

cors_origins = [o.strip() for o in cors_origins_raw.split(',') if o.strip()]

# A wildcard origin must not be combined with credentialed requests: the auth
# cookie is SameSite=None, so allowing every origin while sending credentials
# would let any site read authenticated API responses. Require an explicit
# origin allowlist instead of silently reflecting every origin.
if '*' in cors_origins:
    raise RuntimeError(
        "CORS_ORIGINS='*' cannot be combined with credentialed auth cookies; "
        "set an explicit comma-separated origin allowlist"
    )

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/")
async def root():
    return {"message": "Multi-Model Hub API", "version": "v1.0.2-S9", "spec": "interdependentway.org/canon/spec.md"}


@app.get("/api/ai-instructions")
async def ai_instructions_json():
    return get_ai_instruction_payload()


@app.get("/ai-instructions.txt", response_class=PlainTextResponse)
async def ai_instructions_txt():
    return get_ai_instruction_text()


@app.get("/health")
async def health_liveness():
    return {"status": "ok", "build": "v1.0.2-S9"}


@app.get("/api/health")
async def api_health_liveness():
    return {"status": "ok", "build": "v1.0.2-S9"}


@app.get("/ready")
@app.get("/api/ready")
async def ready_check():
    mongo_ok, mongo_message = await _check_mongo_ready()
    payload = {
        "status": "ready" if mongo_ok else "not_ready",
        "build": "v1.0.2-S9",
        "checks": {
            "mongo": {
                "ok": mongo_ok,
                "message": mongo_message,
            }
        },
        "startup_time": app.state.startup_time,
    }
    if mongo_ok:
        return payload
    return JSONResponse(status_code=503, content=payload)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
# ratios: loc_comments=99:3 imports_exports=23:7 calls_definitions=37:8
