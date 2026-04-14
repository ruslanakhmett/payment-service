from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=True,
    )

    url: str = Field(validation_alias="PG_URL")


class RabbitMQSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=True,
    )

    url: str = Field(validation_alias="RABBITMQ_URL")
    payments_new_queue: str = Field(
        default="payments.new", validation_alias="RABBITMQ_PAYMENTS_NEW_QUEUE"
    )

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=True,
    )

    poll_interval_s: float = Field(default=1.0, validation_alias="OUTBOX_POLL_INTERVAL_S")
    batch_size: int = Field(default=50, validation_alias="OUTBOX_BATCH_SIZE")
    max_attempts: int = Field(default=3, validation_alias="OUTBOX_MAX_ATTEMPTS")
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)


settings = Settings()
