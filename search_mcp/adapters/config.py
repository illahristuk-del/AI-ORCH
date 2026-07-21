from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_host: str
    db_port: str
    db_name: str
    db_user: str
    db_pass: str

    mcp_url: str = "http://localhost:8000/mcp"
    calendar_mcp_url: str

    anthropic_api_key: str

    hr_agent_url: str
    calendar_agent_url: str

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()  # type: ignore[call-arg]
