import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AGENT_NAME: str = "{{AGENT_NAME}}"
    ENV: str = "development"
    LOG_LEVEL: str = "info"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # Adrian Security Settings
    ADRIAN_API_KEY: str = "adr_live_default_key"
    SECURITY_MODE: str = "block" # audit, hitl, block
    PII_SCRUB_ENABLED: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
