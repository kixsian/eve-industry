"""
Public ESI endpoints for industry cost calculation.
No auth required - adjusted prices and system cost indices are public.
"""
import httpx
import time
from typing import Dict, Optional

ESI_BASE = "https://esi.evetech.net/latest"

# Cache adjusted prices for 24h (updated daily by CCP)
_adjusted_prices: Optional[Dict[int, float]] = None
_adjusted_prices_expiry: float = 0

# Cache system cost indices for 1h (updated hourly by CCP)
_system_indices: Optional[Dict[int, float]] = None
_system_indices_expiry: float = 0


async def get_adjusted_prices() -> Dict[int, float]:
    """Return {type_id: adjusted_price} for all items. Cached 24h."""
    global _adjusted_prices, _adjusted_prices_expiry
    if _adjusted_prices is not None and time.time() < _adjusted_prices_expiry:
        return _adjusted_prices

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ESI_BASE}/markets/prices/", timeout=30)
        response.raise_for_status()
        data = response.json()

    prices = {
        item["type_id"]: item["adjusted_price"]
        for item in data
        if "adjusted_price" in item
    }
    _adjusted_prices = prices
    _adjusted_prices_expiry = time.time() + 86400
    return prices


async def get_system_cost_index(solar_system_id: int) -> float:
    """Return manufacturing cost index for a solar system. Cached 1h."""
    global _system_indices, _system_indices_expiry
    if _system_indices is None or time.time() >= _system_indices_expiry:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ESI_BASE}/industry/systems/", timeout=30)
            response.raise_for_status()
            data = response.json()

        _system_indices = {}
        for system in data:
            for idx in system.get("cost_indices", []):
                if idx["activity"] == "manufacturing":
                    _system_indices[system["solar_system_id"]] = idx["cost_index"]
                    break

        _system_indices_expiry = time.time() + 3600

    return _system_indices.get(solar_system_id, 0.0)
