# 🧠 Core Module Documentation

> The brain 🧠 of our operation! This module contains all the fundamental components that power the Pyramid-Tracker.

## 🔢 Constants (`constants.py`)

Our constants are like the trusty sidekicks that keep everything organized! 🦸‍♂️

```python
class Platform(Enum):
    CODECHEF = "CodeChef"
    CODEFORCES = "Codeforces"
    # ...and more!
```

- **Platform**: Different competitive programming platforms we support
- **College**: Educational institutions our participants belong to
- **Batch**: Graduation years of our participants

## ⚙️ Configuration (`config.py`)

Configuration is king! 👑 This is where we set up all the secret sauce of our application.

```python
class Settings(BaseSettings):
    log: LoggingSettings = LoggingSettings()
    db: DatabaseSettings = DatabaseSettings()
    api: APICredentials = APICredentials()
    url: URLSettings = URLSettings()
```

- **LoggingSettings**: How we track what's happening
- **DatabaseSettings**: MongoDB connection info
- **APICredentials**: Keys to unlock the platform APIs
- **URLSettings**: Where to find everything on the web

## 📝 Logging (`logging.py`)

Who needs a diary when you have a structured logger? 📔

```python
def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
```

Our logging setup uses the awesome `structlog` library for beautiful, structured logs that make debugging a breeze! 🌊

## ❌ Exceptions (`exceptions.py`)

When things go wrong, we don't panic - we have custom exceptions! 😱

```python
class ScraperError(Exception):
    """Base class for scraper errors"""
    pass
```

- **ScraperError**: Base exception for all scraping issues
- **RateLimitError**: When platforms say "slow down, buddy!" 🛑
- **UserNotFoundError**: When we can't find a user on a platform
- **DatabaseError**: When database operations get cranky

## 📄 YAML Configuration Files

Our YAML files are like treasure maps! 🗺️

- **contests.yaml**: Details about competitive programming contests
- **user_details.yaml**: Configuration for user batches and colleges

## 🔍 How to Use the Core Module

The core module is imported across the entire application:

```python
from core.constants import Platform
from core.logging import get_logger
from core.config import get_settings
from core.exceptions import ScraperError
```

## 🧪 Pro Tips

- Always use the enum values from `constants.py` instead of hardcoding strings
- Access configuration with the `get_settings()` function (it's cached for performance!)
- Get a logger with `get_logger(__name__)` at the top of your modules
- Catch specific exceptions for better error handling

---

Remember, the core module is like the foundation of a house - if it's solid, everything else will be too! 🏠 