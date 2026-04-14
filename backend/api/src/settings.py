from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=True,
    )

    host: str = Field(validation_alias="POSTGRES_HOST")
    port: int = Field(validation_alias="POSTGRES_PORT")
    db: str = Field(validation_alias="POSTGRES_DB_PROD")
    user: str = Field(validation_alias="POSTGRES_USER_PROD")
    password: str = Field(validation_alias="POSTGRES_PASSWORD_PROD")

    @property
    def pg_url(self) -> str:
        safe_password = quote_plus(self.password)  # экранирование
        return f"postgresql+asyncpg://{self.user}:{safe_password}@{self.host}:{self.port}/{self.db}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=True,
    )

    api_port: int = Field(default=5000, validation_alias="API_PORT")
    domain_url: str = Field(default="localhost", validation_alias="DOMAIN_URL")
    api_key: str = Field(default="dev_api_key_change_me", validation_alias="API_KEY")

    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    postgres: PostgresSettings = Field(default_factory=PostgresSettings)


settings = Settings()