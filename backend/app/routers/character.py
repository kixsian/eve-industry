from fastapi import APIRouter, HTTPException
from ..services import esi_service
from ..services.sde_service import get_sde_service

router = APIRouter(prefix="/api/character", tags=["character"])


@router.get("/info")
async def get_info():
    try:
        return await esi_service.get_character_info()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wallet")
async def get_wallet():
    try:
        balance = await esi_service.get_wallet_balance()
        return {"balance": balance}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skills")
async def get_skills():
    try:
        return await esi_service.get_skills()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def get_jobs():
    try:
        return await esi_service.get_industry_jobs()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets")
async def get_assets():
    try:
        return await esi_service.get_assets()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corporation/jobs")
async def get_corporation_jobs():
    try:
        jobs = await esi_service.get_corporation_jobs()
        # Resolve blueprint and product type IDs to names via SDE
        sde = get_sde_service()
        type_ids = list({j["blueprint_type_id"] for j in jobs} | {j.get("product_type_id") for j in jobs if j.get("product_type_id")})
        names = sde.get_type_names(type_ids)
        for job in jobs:
            job["blueprint_name"] = names.get(job["blueprint_type_id"], f"#{job['blueprint_type_id']}")
            if job.get("product_type_id"):
                job["product_name"] = names.get(job["product_type_id"], f"#{job['product_type_id']}")
        return jobs
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corporation/assets")
async def get_corporation_assets():
    try:
        return await esi_service.get_corporation_assets()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
