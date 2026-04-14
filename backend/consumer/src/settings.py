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
    payments_new_dlq_queue: str = Field(
        default="payments.new.dlq",
        validation_alias="RABBITMQ_PAYMENTS_NEW_DLQ_QUEUE",
    )

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=True,
    )

    consumer_port: int = Field(default=5001, validation_alias="CONSUMER_PORT")
    max_webhook_attempts: int = Field(default=3, validation_alias="MAX_WEBHOOK_ATTEMPTS")
    max_message_attempts: int = Field(default=3, validation_alias="MAX_MESSAGE_ATTEMPTS")
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)


settings = Settings()
