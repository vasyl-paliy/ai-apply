"""Configuration settings for AutoApply AI."""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="AutoApply AI", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=4096, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    # Email
    gmail_client_id: Optional[str] = Field(default=None, env="GMAIL_CLIENT_ID")
    gmail_client_secret: Optional[str] = Field(default=None, env="GMAIL_CLIENT_SECRET")
    gmail_refresh_token: Optional[str] = Field(default=None, env="GMAIL_REFRESH_TOKEN")
    gmail_email_address: Optional[str] = Field(default=None, env="GMAIL_EMAIL_ADDRESS")
    
    # SMTP Settings
    smtp_server: str = Field(default="smtp.gmail.com", env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    from_email: str = Field(default="", env="FROM_EMAIL")
    from_name: str = Field(default="AutoApply AI", env="FROM_NAME")
    
    # Job Boards
    linkedin_email: Optional[str] = Field(default=None, env="LINKEDIN_EMAIL")
    linkedin_password: Optional[str] = Field(default=None, env="LINKEDIN_PASSWORD")
    indeed_api_key: Optional[str] = Field(default=None, env="INDEED_API_KEY")
    glassdoor_api_key: Optional[str] = Field(default=None, env="GLASSDOOR_API_KEY")
    
    # Contact Finding
    hunter_io_api_key: Optional[str] = Field(default=None, env="HUNTER_IO_API_KEY")
    clearbit_api_key: Optional[str] = Field(default=None, env="CLEARBIT_API_KEY")
    apollo_api_key: Optional[str] = Field(default=None, env="APOLLO_API_KEY")
    
    # Notifications
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="ALLOWED_ORIGINS"
    )
    allowed_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="ALLOWED_METHODS"
    )
    allowed_headers: List[str] = Field(default=["*"], env="ALLOWED_HEADERS")
    
    # File Storage
    upload_dir: str = Field(default="uploads/", env="UPLOAD_DIR")
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: List[str] = Field(
        default=["pdf", "doc", "docx", "txt"],
        env="ALLOWED_EXTENSIONS"
    )
    
    # Scraping
    scraping_delay: int = Field(default=2, env="SCRAPING_DELAY")
    max_concurrent_scrapes: int = Field(default=5, env="MAX_CONCURRENT_SCRAPES")
    user_agent: str = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        env="USER_AGENT"
    )
    headless_browser: bool = Field(default=True, env="HEADLESS_BROWSER")
    browser_timeout: int = Field(default=30, env="BROWSER_TIMEOUT")
    
    # Application Limits
    max_applications_per_day: int = Field(default=20, env="MAX_APPLICATIONS_PER_DAY")
    max_cover_letters_per_hour: int = Field(default=10, env="MAX_COVER_LETTERS_PER_HOUR")
    min_match_score: float = Field(default=0.7, env="MIN_MATCH_SCORE")
    
    # Dashboard
    dashboard_items_per_page: int = Field(default=20, env="DASHBOARD_ITEMS_PER_PAGE")
    session_timeout: int = Field(default=3600, env="SESSION_TIMEOUT")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8001, env="METRICS_PORT")
    
    # Development
    reload: bool = Field(default=True, env="RELOAD")
    workers: int = Field(default=1, env="WORKERS")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Playwright
    playwright_headless: bool = Field(default=True, env="PLAYWRIGHT_HEADLESS")
    playwright_timeout: int = Field(default=30000, env="PLAYWRIGHT_TIMEOUT")
    playwright_slow_mo: int = Field(default=0, env="PLAYWRIGHT_SLOW_MO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings() 