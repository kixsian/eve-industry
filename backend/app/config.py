from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://eve_calc:eve_calc_dev@localhost:5432/eve_industry"
    eve_client_id: Optional[str] = None
    eve_client_secret: Optional[str] = None
    eve_callback_url: str = "http://localhost:3000/auth/callback"
    eve_sso_url: str = "https://login.eveonline.com/v2/oauth"
    eve_esi_url: str = "https://esi.eveonline.com/latest"
    fuzzwork_api_url: str = "https://market.fuzzwork.co.uk/api"
    sde_path: str = "sde/eve.db"
    secret_key: str = "dev-secret-key-change-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
