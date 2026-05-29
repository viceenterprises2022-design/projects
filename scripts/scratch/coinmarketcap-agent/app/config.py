from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AGENT_NAME: str = "Coinmarketcap Agent"
    ENV: str = "development"
    LOG_LEVEL: str = "info"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    CMC_MCP_URL: str = "https://mcp.coinmarketcap.com/mcp"
    CMC_SKILL_HUB_URL: str = "https://mcp.coinmarketcap.com/skill-hub/stream"
    CMC_API_KEY: str = "7f165fb95f174e6381a0d98391e1e53b"

    # Adrian Security Settings
    ADRIAN_API_KEY: str = "adr_live_default_key"
    SECURITY_MODE: str = "block"
    PII_SCRUB_ENABLED: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
