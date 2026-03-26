from fastapi import APIRouter, HTTPException
from ..services import esi_service

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
