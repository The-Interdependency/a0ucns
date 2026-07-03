# ratios: loc_comments=192:8 imports_exports=8:9 calls_definitions=81:10
"""Model registry management — add/remove developers and models."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from db import db
from models.registry import VerificationResponse, VerifyModelRequest
from models.v1 import AddDeveloperRequest, AddModelRequest, RegistryResponse, DeveloperDef, ModelDef
from services.auth import get_current_user, get_user_id
from services.llm import (
    DEFAULT_REGISTRY,
    UNIVERSAL_DEVELOPER_IDS,
    model_default_payload,
    reconcile_registry_developers,
    universal_managed_model_ids,
)
from services.registry_verifier import verify_developer_models, verify_registry, verify_single_model

router = APIRouter(prefix="/api/v1/registry", tags=["registry"])


async def _get_or_seed_registry(user_id: str) -> dict:
    """Get user's registry doc, seeding from defaults if missing."""
    doc = await db.model_registry.find_one({"user_id": user_id}, {"_id": 0})
    if doc:
        developers, changed = reconcile_registry_developers(doc.get("developers", {}))
        if changed:
            doc["developers"] = developers
            doc["updated_at"] = datetime.now(timezone.utc).isoformat()
            await db.model_registry.update_one(
                {"user_id": user_id},
                {"$set": {"developers": developers, "updated_at": doc["updated_at"]}},
            )
        return doc
    # Seed from defaults
    seed = {
        "user_id": user_id,
        "developers": reconcile_registry_developers(DEFAULT_REGISTRY)[0],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.model_registry.insert_one(seed)
    seed.pop("_id", None)
    return seed


@router.get("", response_model=RegistryResponse)
async def get_registry(current_user: dict = Depends(get_current_user)):
    """Get the user's model registry."""
    uid = get_user_id(current_user)
    doc = await _get_or_seed_registry(uid)
    devs = doc.get("developers", {})

    result = []
    for dev_id, dev in devs.items():
        models = []
        for m in dev.get("models", []):
            if isinstance(m, dict):
                models.append(ModelDef(model_id=m["model_id"], display_name=m.get("display_name"), enabled=m.get("enabled", True)))
            else:
                models.append(ModelDef(model_id=m))
        result.append(DeveloperDef(
            developer_id=dev_id,
            name=dev.get("name", dev_id),
            auth_type=dev.get("auth_type", "emergent"),
            base_url=dev.get("base_url"),
            website=dev.get("website"),
            models=models,
        ))

    return RegistryResponse(developers=result)


@router.get("/defaults")
async def get_registry_model_defaults(current_user: dict = Depends(get_current_user)):
    uid = get_user_id(current_user)
    doc = await _get_or_seed_registry(uid)
    developers = doc.get("developers", {})
    result = {}
    for developer_id, developer in developers.items():
        models = developer.get("models", [])
        result[developer_id] = {
            "models": {
                model.get("model_id"): model_default_payload(developer_id, model.get("model_id"))
                for model in models
                if isinstance(model, dict) and model.get("model_id")
            }
        }
    return {"defaults": result}


@router.post("/developer")
async def add_developer(
    request: AddDeveloperRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add a new developer to the registry."""
    uid = get_user_id(current_user)
    doc = await _get_or_seed_registry(uid)

    if request.developer_id in doc.get("developers", {}):
        raise HTTPException(status_code=400, detail="Developer already exists")

    new_dev = {
        "name": request.name,
        "auth_type": request.auth_type,
        "base_url": request.base_url,
        "website": request.website,
        "models": [m.model_dump() for m in request.models],
    }

    await db.model_registry.update_one(
        {"user_id": uid},
        {
            "$set": {
                f"developers.{request.developer_id}": new_dev,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
    return {"message": f"Developer {request.developer_id} added", "developer": new_dev}


@router.post("/developer/{developer_id}/model")
async def add_model(
    developer_id: str,
    request: AddModelRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add a model to an existing developer."""
    uid = get_user_id(current_user)
    doc = await _get_or_seed_registry(uid)

    if developer_id not in doc.get("developers", {}):
        raise HTTPException(status_code=404, detail="Developer not found")

    developer = doc["developers"].get(developer_id, {})
    if developer.get("auth_type") == "emergent":
        allowed_model_ids = universal_managed_model_ids(developer_id)
        if request.model_id not in allowed_model_ids:
            raise HTTPException(status_code=400, detail="This universal-key registry is curated. Only supported universal-key models are allowed for this developer.")
        if any(model.get("model_id") == request.model_id for model in developer.get("models", []) if isinstance(model, dict)):
            raise HTTPException(status_code=400, detail="Model already exists")

    model_entry = {"model_id": request.model_id, "display_name": request.display_name, "enabled": True}

    await db.model_registry.update_one(
        {"user_id": uid},
        {
            "$push": {f"developers.{developer_id}.models": model_entry},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )
    return {"message": f"Model {request.model_id} added to {developer_id}"}


@router.delete("/developer/{developer_id}/model/{model_id}")
async def remove_model(
    developer_id: str,
    model_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Remove a model from a developer."""
    uid = get_user_id(current_user)
    doc = await _get_or_seed_registry(uid)
    developer = doc.get("developers", {}).get(developer_id, {})
    if developer_id in UNIVERSAL_DEVELOPER_IDS or developer.get("auth_type") == "emergent":
        raise HTTPException(status_code=400, detail="Universal-key-compatible registry models are managed automatically and cannot be removed.")
    await db.model_registry.update_one(
        {"user_id": uid},
        {
            "$pull": {f"developers.{developer_id}.models": {"model_id": model_id}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )
    return {"message": f"Model {model_id} removed from {developer_id}"}


@router.delete("/developer/{developer_id}")
async def remove_developer(
    developer_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Remove a developer from the registry."""
    uid = get_user_id(current_user)
    if developer_id in UNIVERSAL_DEVELOPER_IDS:
        raise HTTPException(status_code=400, detail="Universal-key-compatible developers are managed automatically and cannot be removed.")
    await db.model_registry.update_one(
        {"user_id": uid},
        {
            "$unset": {f"developers.{developer_id}": ""},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )
    return {"message": f"Developer {developer_id} removed"}


@router.post("/verify/model", response_model=VerificationResponse)
async def verify_registry_model(
    request: VerifyModelRequest,
    current_user: dict = Depends(get_current_user),
):
    uid = get_user_id(current_user)
    doc = await _get_or_seed_registry(uid)
    registry = doc.get("developers", {})
    result = await verify_single_model(current_user, registry, request.developer_id, request.model_id, mode=request.mode)
    return VerificationResponse(
        scope="model",
        verification_mode=request.mode,
        verified_count=1 if result.status in {"verified", "verified_via_provider"} else 0,
        total_count=1,
        results=[result],
    )


@router.post("/verify/developer/{developer_id}", response_model=VerificationResponse)
async def verify_registry_developer(
    developer_id: str,
    current_user: dict = Depends(get_current_user),
):
    uid = get_user_id(current_user)
    doc = await _get_or_seed_registry(uid)
    registry = doc.get("developers", {})
    return await verify_developer_models(current_user, registry, developer_id, mode="light")


@router.post("/verify/all", response_model=VerificationResponse)
async def verify_registry_all(current_user: dict = Depends(get_current_user)):
    uid = get_user_id(current_user)
    doc = await _get_or_seed_registry(uid)
    registry = doc.get("developers", {})
    return await verify_registry(current_user, registry, mode="light")
# ratios: loc_comments=192:8 imports_exports=8:9 calls_definitions=81:10
