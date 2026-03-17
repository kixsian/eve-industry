"""
Market price service using Fuzzwork Market API.
"""
import httpx
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from ..config import settings


class PriceCache:
    """Simple in-memory price cache with TTL."""
    def __init__(self, ttl_minutes: int = 30):
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache: Dict[int, tuple] = {}  # type_id -> (price, timestamp)

    def get(self, type_id: int) -> Optional[float]:
        if type_id in self.cache:
            price, timestamp = self.cache[type_id]
            if datetime.now() - timestamp < self.ttl:
                return price
            else:
                del self.cache[type_id]
        return None

    def set(self, type_id: int, price: float):
        self.cache[type_id] = (price, datetime.now())

    def set_bulk(self, prices: Dict[int, float]):
        for type_id, price in prices.items():
            self.set(type_id, price)


class MarketService:
    """
    Service for fetching market prices from Fuzzwork API.
    Fuzzwork API: https://market.fuzzwork.co.uk/api/
    Returns: {"typeID": {"buy": {"max": 100.0}, "sell": {"min": 105.0}}, ...}
    """
    def __init__(self, api_url: str = None, cache_ttl_minutes: int = 30):
        self.api_url = api_url or settings.fuzzwork_api_url
        self.cache = PriceCache(ttl_minutes=cache_ttl_minutes)
        self.client = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient()
        return self.client

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def get_prices(self, type_ids: List[int]) -> Dict[int, float]:
        """
        Get prices for a list of type IDs.
        Returns dict of {type_id: sell_min_price}
        Falls back to cached values if available.
        """
        # Check cache first
        cached = {}
        to_fetch = []
        for type_id in type_ids:
            cached_price = self.cache.get(type_id)
            if cached_price is not None:
                cached[type_id] = cached_price
            else:
                to_fetch.append(type_id)

        if not to_fetch:
            return cached

        # Fetch from API
        fetched = await self._fetch_from_api(to_fetch)
        self.cache.set_bulk(fetched)

        return {**cached, **fetched}

    async def _fetch_from_api(self, type_ids: List[int]) -> Dict[int, float]:
        """
        Fetch prices from Fuzzwork API.
        API endpoint: /types/prices/?typeid=123,456,789
        """
        if not type_ids:
            return {}

        client = await self._get_client()
        type_ids_str = ",".join(str(tid) for tid in type_ids)

        try:
            url = f"{self.api_url}/types/prices/?typeid={type_ids_str}"
            response = await client.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            prices = {}

            for type_id_str, type_data in data.items():
                try:
                    type_id = int(type_id_str)
                    # Use sell.min (lowest sell price at Jita)
                    sell_data = type_data.get("sell", {})
                    min_price = sell_data.get("min")
                    if min_price is not None:
                        prices[type_id] = min_price
                except (ValueError, KeyError):
                    continue

            return prices

        except httpx.HTTPError as e:
            print(f"Error fetching prices from Fuzzwork: {e}")
            return {}

    async def get_single_price(self, type_id: int) -> Optional[float]:
        """Get price for a single type."""
        prices = await self.get_prices([type_id])
        return prices.get(type_id)

    async def search_prices(self, type_ids: List[int]) -> Dict[int, Dict]:
        """
        Get detailed price info (buy/sell, max/min).
        """
        client = await self._get_client()
        type_ids_str = ",".join(str(tid) for tid in type_ids)

        try:
            url = f"{self.api_url}/types/prices/?typeid={type_ids_str}"
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching detailed prices: {e}")
            return {}


# Singleton
_market_service = None


async def get_market_service() -> MarketService:
    global _market_service
    if _market_service is None:
        _market_service = MarketService()
    return _market_service
