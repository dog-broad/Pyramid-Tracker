import os
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError
from functools import lru_cache
from typing import Dict, List
from core.exceptions import ConfigError
from dotenv import load_dotenv  # Importing load_dotenv from python-dotenv


# ==============================
# Load environment variables from .env file
# ==============================
def load_env():
    """Load environment variables from .env file."""
    dotenv_path = Path(".env")
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print("Warning: .env file not found.")


# ==============================
# Helper function for prefix-based environment variable fetching
# ==============================
def get_env_variable(name: str, prefix: str = "") -> str:
    """Fetches an environment variable with an optional prefix."""
    env_var_name = f"{prefix}{name}"
    return os.getenv(env_var_name)


# ==============================
# Logging Configuration
# ==============================
class LoggingSettings(BaseModel):
    log_debug: bool = Field(...)

    @classmethod
    def from_env(cls, prefix: str = "LOG_") -> 'LoggingSettings':
        return cls(log_debug=bool(get_env_variable("DEBUG", prefix)))


# ==============================
# Database Configuration
# ==============================
class DatabaseSettings(BaseModel):
    mongodb_uri: str = Field(...)
    mongodb_password: str = Field(...)
    mongodb_cache_name: str = Field(...)

    @classmethod
    def from_env(cls, prefix: str = "DB_") -> 'DatabaseSettings':
        return cls(
            mongodb_uri=get_env_variable("MONGODB_URI", prefix),
            mongodb_password=get_env_variable("MONGODB_PASSWORD", prefix),
            mongodb_cache_name=get_env_variable("MONGODB_CACHE_NAME", prefix)
        )


# ==============================
# API Credentials Configuration
# ==============================
class APICredentials(BaseModel):
    codeforces_key: str = Field(...)
    codeforces_secret: str = Field(...)
    codechef_client_id: str = Field(...)
    codechef_client_secret: str = Field(...)
    gfg_username: str = Field(...)
    gfg_password: str = Field(...)
    git_username: str = Field(...)
    git_password: str = Field(...)

    @classmethod
    def from_env(cls, prefix: str = "API_") -> 'APICredentials':
        return cls(
            codeforces_key=get_env_variable("CODEFORCES_KEY", prefix),
            codeforces_secret=get_env_variable("CODEFORCES_SECRET", prefix),
            codechef_client_id=get_env_variable("CODECHEF_CLIENT_ID", prefix),
            codechef_client_secret=get_env_variable("CODECHEF_CLIENT_SECRET", prefix),
            gfg_username=get_env_variable("GFG_USERNAME", prefix),
            gfg_password=get_env_variable("GFG_PASSWORD", prefix),
            git_username=get_env_variable("GIT_USERNAME", prefix),
            git_password=get_env_variable("GIT_PASSWORD", prefix)
        )


# ==============================
# URL Configuration
# ==============================
class URLSettings(BaseModel):
    codechef_api_url: str = Field(...)
    codechef_url: str = Field(...)
    codeforces_url: str = Field(...)
    geeksforgeeks_url: str = Field(...)
    gfg_api_url: str = Field(...)
    gfg_practice_url: str = Field(...)
    gfg_weekly_contest_url: str = Field(...)
    hackerrank_api_url: str = Field(...)
    hackerrank_url: str = Field(...)
    leetcode_url: str = Field(...)

    @classmethod
    def from_env(cls, prefix: str = "URL_") -> 'URLSettings':
        return cls(
            codechef_api_url=get_env_variable("CODECHEF_API_URL", prefix),
            codechef_url=get_env_variable("CODECHEF_URL", prefix),
            codeforces_url=get_env_variable("CODEFORCES_URL", prefix),
            geeksforgeeks_url=get_env_variable("GEEKSFORGEEKS_URL", prefix),
            gfg_api_url=get_env_variable("GFG_API_URL", prefix),
            gfg_practice_url=get_env_variable("GFG_PRACTICE_URL", prefix),
            gfg_weekly_contest_url=get_env_variable("GFG_WEEKLY_CONTEST_URL", prefix),
            hackerrank_api_url=get_env_variable("HACKERRANK_API_URL", prefix),
            hackerrank_url=get_env_variable("HACKERRANK_URL", prefix),
            leetcode_url=get_env_variable("LEETCODE_URL", prefix)
        )


# ==============================
# Full Settings Configuration
# ==============================
class Settings(BaseModel):
    log: LoggingSettings
    db: DatabaseSettings
    api: APICredentials
    url: URLSettings

    @classmethod
    def from_env(cls) -> 'Settings':
        return cls(
            log=LoggingSettings.from_env(prefix="LOG_"),
            db=DatabaseSettings.from_env(prefix="DB_"),
            api=APICredentials.from_env(prefix="API_"),
            url=URLSettings.from_env(prefix="URL_")
        )


# ==============================
# Caching Settings Access
# ==============================
@lru_cache()
def get_settings() -> Settings:
    try:
        load_env()  # Load the environment variables before accessing settings
        return Settings.from_env()
    except ValidationError as e:
        raise ConfigError(f"Failed to load settings: {e}")
