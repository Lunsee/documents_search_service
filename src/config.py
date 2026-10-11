from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    search_limit: int = 20
    log_level: str = "INFO"

    postgres_user: str = "search"
    postgres_password: str = "search"
    postgres_db: str = "search"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    es_url: str = "http://localhost:9200"
    es_index: str = "documents"

    data_path: str = "data/posts.csv"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
