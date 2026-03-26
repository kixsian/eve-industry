"""
ESI API service. Fetches character data using stored tokens.
"""
import httpx
from typing import List
from .auth_service import get_valid_token, get_current_character

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
