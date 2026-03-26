from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    eve_client_id: Optional[str] = None
    eve_client_secret: Optional[str] = None
    eve_callback_url: str = "http://localhost:8000/auth/callback"
    eve_frontend_url: str = "http://localhost:5173"
    eve_sso_url: str = "https://login.eveonline.com/v2/oauth"
    eve_esi_url: str = "https://esi.evetech.net/latest"
    sde_path: str = "sde/eve.db"
    secret_key: str = "dev-secret-key-change-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
