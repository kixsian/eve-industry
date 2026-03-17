"""
Market price service using CCP ESI API.
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
    Service for fetching market prices from CCP ESI API.
    ESI API: https://esi.eveonline.com/latest/

    Uses two strategies:
    1. Bulk cache: all average prices from /markets/prices/ (1 hour TTL)
    2. Jita orders: per-type sell orders from /markets/10000002/orders/ (30 min TTL)
    """

    JITA_REGION_ID = 10000002
    JITA_STATION_ID = 60003760
    BULK_CACHE_TTL = 60  # minutes
    JITA_CACHE_TTL = 30  # minutes

    def __init__(self, esi_url: str = None):
        self.esi_url = esi_url or settings.eve_esi_url
        self.per_type_cache = PriceCache(ttl_minutes=self.JITA_CACHE_TTL)
        self.client = None
        self._bulk_cache: Dict[int, float] = {}
        self._bulk_cache_time: Optional[datetime] = None

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

        Fetch flow:
        1. Check per-type cache (Jita orders)
        2. Fetch Jita sell orders concurrently for uncached types
        3. Filter to Jita 4-4 station (location_id 60003760), take min price
        4. Fall back to bulk average price if no Jita orders
        5. Return cached/fetched prices
        """
        # Check cache first
        cached = {}
        to_fetch = []
        for type_id in type_ids:
            cached_price = self.per_type_cache.get(type_id)
            if cached_price is not None:
                cached[type_id] = cached_price
            else:
                to_fetch.append(type_id)

        if not to_fetch:
            return cached

        # Fetch Jita orders concurrently for uncached types
        fetched = await self._fetch_jita_prices(to_fetch)
        self.per_type_cache.set_bulk(fetched)

        return {**cached, **fetched}

    async def _fetch_jita_prices(self, type_ids: List[int]) -> Dict[int, float]:
        """
        Fetch prices from Jita orders on ESI.
        For each type_id, queries /markets/{region_id}/orders/?type_id={id}&order_type=sell
        Filters to Jita 4-4 station (location_id 60003760), takes minimum price.
        Falls back to bulk average price if no Jita orders.
        """
        if not type_ids:
            return {}

        # Fetch concurrently
        tasks = [self._fetch_single_type_price(tid) for tid in type_ids]
        prices = await asyncio.gather(*tasks, return_exceptions=True)

        result = {}
        for type_id, price in zip(type_ids, prices):
            if isinstance(price, Exception):
                # If exception occurred, try bulk cache fallback
                bulk_price = await self._get_bulk_price(type_id)
                result[type_id] = bulk_price or 0.0
            elif price is not None:
                result[type_id] = price
            else:
                # No Jita orders, try bulk cache
                bulk_price = await self._get_bulk_price(type_id)
                result[type_id] = bulk_price or 0.0

        return result

    async def _fetch_single_type_price(self, type_id: int) -> Optional[float]:
        """
        Fetch Jita sell orders for a single type.
        Returns minimum sell price at Jita 4-4 station, or None if no orders.
        """
        client = await self._get_client()

        try:
            url = f"{self.esi_url}/markets/{self.JITA_REGION_ID}/orders/"
            params = {
                "type_id": type_id,
                "order_type": "sell",
            }
            print(f"DEBUG: Fetching Jita orders for type {type_id} from {url}")
            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()

            orders = response.json()
            print(f"DEBUG: Got {len(orders)} orders for type {type_id}")

            # Filter to Jita 4-4 station (location_id 60003760)
            jita_orders = [
                o for o in orders
                if o.get("location_id") == self.JITA_STATION_ID
            ]

            if not jita_orders:
                print(f"DEBUG: No Jita 4-4 orders for type {type_id}")
                return None

            # Return minimum sell price
            min_price = min(o.get("price", float("inf")) for o in jita_orders)
            print(f"DEBUG: Type {type_id} min Jita price: {min_price}")
            return min_price

        except httpx.HTTPError as e:
            print(f"ERROR fetching Jita orders for type {type_id}: {e}")
            return None
        except Exception as e:
            print(f"ERROR (unexpected) fetching Jita orders for type {type_id}: {e}")
            return None

    async def _get_bulk_price(self, type_id: int) -> Optional[float]:
        """
        Get bulk average price from ESI /markets/prices/ endpoint.
        Caches all prices for 1 hour.
        """
        # Check if bulk cache is still valid
        if self._bulk_cache_time and (datetime.now() - self._bulk_cache_time) < timedelta(minutes=self.BULK_CACHE_TTL):
            price = self._bulk_cache.get(type_id)
            print(f"DEBUG: Got cached bulk price for type {type_id}: {price}")
            return price

        # Fetch all prices
        client = await self._get_client()
        try:
            url = f"{self.esi_url}/markets/prices/"
            print(f"DEBUG: Fetching bulk prices from {url}")
            response = await client.get(url, timeout=10)
            response.raise_for_status()

            prices_data = response.json()
            print(f"DEBUG: Got {len(prices_data)} bulk prices")

            # Parse response: list of {"type_id": X, "adjusted_price": Y, "average_price": Z}
            self._bulk_cache = {}
            for item in prices_data:
                tid = item.get("type_id")
                # Use average_price (actual market average)
                price = item.get("average_price")
                if tid and price:
                    self._bulk_cache[tid] = price

            self._bulk_cache_time = datetime.now()
            bulk_price = self._bulk_cache.get(type_id)
            print(f"DEBUG: Type {type_id} bulk price: {bulk_price}")
            return bulk_price

        except httpx.HTTPError as e:
            print(f"ERROR fetching bulk prices: {e}")
            return None
        except Exception as e:
            print(f"ERROR (unexpected) fetching bulk prices: {e}")
            return None

    async def get_single_price(self, type_id: int) -> Optional[float]:
        """Get price for a single type."""
        prices = await self.get_prices([type_id])
        return prices.get(type_id)


# Singleton
_market_service = None


async def get_market_service() -> MarketService:
    global _market_service
    if _market_service is None:
        _market_service = MarketService()
    return _market_service
