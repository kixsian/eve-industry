"""
Market price service using Fuzzwork aggregates API.
https://market.fuzzwork.co.uk/api/
"""
import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta


FUZZWORK_URL = "https://market.fuzzwork.co.uk/aggregates/"
JITA_STATION_ID = 60003760
CACHE_TTL_MINUTES = 30
CHUNK_SIZE = 200  # Fuzzwork handles large type lists fine, but chunk to be safe


class PriceCache:
    """Simple in-memory price cache with TTL."""
    def __init__(self, ttl_minutes: int = CACHE_TTL_MINUTES):
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache: Dict[int, tuple] = {}  # type_id -> (price, timestamp)

    def get(self, type_id: int) -> Optional[float]:
        if type_id in self.cache:
            price, timestamp = self.cache[type_id]
            if datetime.now() - timestamp < self.ttl:
                return price
            del self.cache[type_id]
        return None

    def set_bulk(self, prices: Dict[int, float]):
        now = datetime.now()
        for type_id, price in prices.items():
            self.cache[type_id] = (price, now)


class MarketService:
    """
    Fetches Jita sell prices from Fuzzwork aggregates API.
    Single bulk call per batch of type IDs, 30-min in-memory cache.
    """

    def __init__(self):
        self.cache = PriceCache()
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
        Get Jita sell prices for a list of type IDs.
        Returns dict of {type_id: min_sell_price}.
        Uses Fuzzwork aggregates API with 30-min cache.
        """
        cached = {}
        to_fetch = []
        for type_id in type_ids:
            price = self.cache.get(type_id)
            if price is not None:
                cached[type_id] = price
            else:
                to_fetch.append(type_id)

        if not to_fetch:
            return cached

        fetched = await self._fetch_fuzzwork_prices(to_fetch)
        self.cache.set_bulk(fetched)

        return {**cached, **fetched}

    async def _fetch_fuzzwork_prices(self, type_ids: List[int]) -> Dict[int, float]:
        """Fetch prices from Fuzzwork in chunks, return {type_id: min_sell_price}."""
        result = {}
        client = await self._get_client()

        for i in range(0, len(type_ids), CHUNK_SIZE):
            chunk = type_ids[i:i + CHUNK_SIZE]
            types_param = ",".join(str(t) for t in chunk)
            try:
                response = await client.get(
                    FUZZWORK_URL,
                    params={"station": JITA_STATION_ID, "types": types_param},
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                for type_id_str, market in data.items():
                    sell = market.get("sell", {})
                    price = sell.get("min")
                    if price is not None:
                        try:
                            result[int(type_id_str)] = float(price)
                        except (ValueError, TypeError):
                            pass
            except Exception as e:
                print(f"ERROR fetching Fuzzwork prices for chunk: {e}")

        return result

    async def get_single_price(self, type_id: int) -> Optional[float]:
        prices = await self.get_prices([type_id])
        return prices.get(type_id)


# Singleton
_market_service = None


async def get_market_service() -> MarketService:
    global _market_service
    if _market_service is None:
        _market_service = MarketService()
    return _market_service
