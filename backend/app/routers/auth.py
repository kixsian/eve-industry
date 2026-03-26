from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from ..services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login():
    """Redirect to EVE SSO login page."""
    return RedirectResponse(auth_service.get_login_url())


@router.get("/callback")
async def callback(code: str, state: str):
    """Handle EVE SSO callback, exchange code for tokens."""
    if not auth_service.verify_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")

    try:
        tokens = await auth_service.exchange_code(code)
        char_info = await auth_service.verify_token(tokens["access_token"])

        auth_service.save_character(
            character_id=char_info["CharacterID"],
            character_name=char_info["CharacterName"],
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=tokens["expires_in"],
        )

        return RedirectResponse("http://localhost:5173?logged_in=true")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auth error: {str(e)}")


@router.get("/logout")
async def logout():
    auth_service.logout()
    return {"status": "logged out"}


@router.get("/status")
async def status():
    """Return current authenticated character, or unauthenticated state."""
    char = auth_service.get_current_character()
    if not char:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "character_id": char["character_id"],
        "character_name": char["character_name"],
        "portrait": f"https://images.evetech.net/characters/{char['character_id']}/portrait?size=64",
    }
