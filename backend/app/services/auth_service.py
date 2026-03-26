"""
EVE SSO OAuth2 service. Handles login flow, token exchange, and token storage.
Tokens are stored in a local SQLite file (sde/auth.db).
"""
import httpx
import base64
import time
import sqlite3
import secrets
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlencode
from ..config import settings

EVE_SSO_AUTH_URL = "https://login.eveonline.com/v2/oauth/authorize"
EVE_SSO_TOKEN_URL = "https://login.eveonline.com/v2/oauth/token"
EVE_VERIFY_URL = "https://esi.eveonline.com/verify/"

SCOPES = [
    "esi-assets.read_assets.v1",
    "esi-skills.read_skills.v1",
    "esi-wallet.read_character_wallet.v1",
    "esi-industry.read_character_jobs.v1",
]

DB_PATH = Path(__file__).parent.parent.parent / "sde" / "auth.db"

# In-memory state store for CSRF protection {state: expiry_timestamp}
_state_store: Dict[str, float] = {}


def init_auth_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            character_id INTEGER PRIMARY KEY,
            character_name TEXT,
            access_token TEXT,
            refresh_token TEXT,
            expires_at REAL
        )
    """)
    conn.commit()
    conn.close()


def get_login_url() -> str:
    state = secrets.token_urlsafe(16)
    _state_store[state] = time.time() + 300  # 5 min TTL
    params = urlencode({
        "response_type": "code",
        "redirect_uri": settings.eve_callback_url,
        "client_id": settings.eve_client_id,
        "scope": " ".join(SCOPES),
        "state": state,
    })
    return f"{EVE_SSO_AUTH_URL}?{params}"


def verify_state(state: str) -> bool:
    expiry = _state_store.pop(state, None)
    return expiry is not None and time.time() < expiry


def _basic_auth_header() -> str:
    credentials = f"{settings.eve_client_id}:{settings.eve_client_secret}"
    return "Basic " + base64.b64encode(credentials.encode()).decode()


async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            EVE_SSO_TOKEN_URL,
            headers={
                "Authorization": _basic_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "authorization_code", "code": code},
        )
        response.raise_for_status()
        return response.json()


async def verify_token(access_token: str) -> dict:
    """Call ESI verify to get character info from an access token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            EVE_VERIFY_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            EVE_SSO_TOKEN_URL,
            headers={
                "Authorization": _basic_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        )
        response.raise_for_status()
        return response.json()


def save_character(character_id: int, character_name: str, access_token: str, refresh_token: str, expires_in: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT OR REPLACE INTO characters
           (character_id, character_name, access_token, refresh_token, expires_at)
           VALUES (?, ?, ?, ?, ?)""",
        (character_id, character_name, access_token, refresh_token, time.time() + expires_in),
    )
    conn.commit()
    conn.close()


def get_current_character() -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM characters ORDER BY expires_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


async def get_valid_token() -> Optional[str]:
    """Return a valid access token, refreshing automatically if needed."""
    char = get_current_character()
    if not char:
        return None

    if time.time() > char["expires_at"] - 60:
        try:
            tokens = await refresh_access_token(char["refresh_token"])
            save_character(
                char["character_id"],
                char["character_name"],
                tokens["access_token"],
                tokens["refresh_token"],
                tokens["expires_in"],
            )
            return tokens["access_token"]
        except Exception:
            return None

    return char["access_token"]


def logout():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM characters")
    conn.commit()
    conn.close()
