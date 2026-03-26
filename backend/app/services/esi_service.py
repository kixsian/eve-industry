"""
ESI API service. Fetches character data using stored tokens.
"""
import httpx
import time
from typing import List, Dict, Optional
from .auth_service import get_valid_token, get_current_character

# Simple in-memory asset cache {type_id: quantity}, expires after 5 minutes
_asset_cache: Optional[Dict[int, int]] = None
_asset_cache_expiry: float = 0

ESI_BASE = "https://esi.evetech.net/latest"

# Industry-relevant skill IDs
INDUSTRY_SKILL_IDS = {
    3380: "Industry",
    3388: "Advanced Industry",
    3396: "Mass Production",
    3397: "Advanced Mass Production",
    3398: "Laboratory Operation",
    3400: "Advanced Laboratory Operation",
    11395: "Metallurgy",
    3409: "Research",
    3413: "Science",
    24625: "Supply Chain Management",
    28578: "Reactions",
}


async def _esi_get(path: str):
    token = await get_valid_token()
    if not token:
        raise ValueError("Not authenticated")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ESI_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()


async def _esi_get_all_pages(path: str) -> List[dict]:
    """Fetch all pages of a paginated ESI endpoint."""
    token = await get_valid_token()
    if not token:
        raise ValueError("Not authenticated")

    all_items = []
    page = 1
    async with httpx.AsyncClient() as client:
        while True:
            sep = "&" if "?" in path else "?"
            response = await client.get(
                f"{ESI_BASE}{path}{sep}page={page}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            all_items.extend(data)
            total_pages = int(response.headers.get("X-Pages", 1))
            if page >= total_pages:
                break
            page += 1

    return all_items


def _require_character() -> dict:
    char = get_current_character()
    if not char:
        raise ValueError("Not authenticated")
    return char


async def get_character_info() -> dict:
    char = _require_character()
    data = await _esi_get(f"/characters/{char['character_id']}/")
    return {
        "character_id": char["character_id"],
        "character_name": char["character_name"],
        "corporation_id": data.get("corporation_id"),
        "portrait": f"https://images.evetech.net/characters/{char['character_id']}/portrait?size=64",
    }


async def get_wallet_balance() -> float:
    char = _require_character()
    return await _esi_get(f"/characters/{char['character_id']}/wallet/")


async def get_skills() -> dict:
    char = _require_character()
    data = await _esi_get(f"/characters/{char['character_id']}/skills/")
    industry_skills = {
        INDUSTRY_SKILL_IDS[s["skill_id"]]: s["trained_skill_level"]
        for s in data.get("skills", [])
        if s["skill_id"] in INDUSTRY_SKILL_IDS
    }
    return {
        "total_sp": data.get("total_sp", 0),
        "industry_skills": industry_skills,
    }


async def get_industry_jobs() -> List[dict]:
    char = _require_character()
    return await _esi_get(f"/characters/{char['character_id']}/industry/jobs/?include_completed=false")


async def get_assets() -> List[dict]:
    char = _require_character()
    return await _esi_get(f"/characters/{char['character_id']}/assets/")


async def get_corporation_id() -> int:
    char = _require_character()
    data = await _esi_get(f"/characters/{char['character_id']}/")
    return data["corporation_id"]


async def get_corporation_jobs() -> List[dict]:
    corp_id = await get_corporation_id()
    return await _esi_get(f"/corporations/{corp_id}/industry/jobs/?include_completed=false")


async def get_corporation_assets() -> List[dict]:
    corp_id = await get_corporation_id()
    return await _esi_get_all_pages(f"/corporations/{corp_id}/assets/")


async def get_corp_asset_quantities() -> Dict[int, int]:
    """
    Return aggregated corp assets as {type_id: total_quantity}.
    Cached for 5 minutes.
    """
    global _asset_cache, _asset_cache_expiry
    if _asset_cache is not None and time.time() < _asset_cache_expiry:
        return _asset_cache

    assets = await get_corporation_assets()
    totals: Dict[int, int] = {}
    for asset in assets:
        if not asset.get("is_singleton"):
            type_id = asset["type_id"]
            totals[type_id] = totals.get(type_id, 0) + asset.get("quantity", 1)

    _asset_cache = totals
    _asset_cache_expiry = time.time() + 300
    return totals
