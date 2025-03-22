# 🌐 Platforms Module Documentation

> The gateway to competitive programming worlds! 🚪 This module contains all the code needed to scrape data from different coding platforms.

## 🏗️ Architecture

The platforms module follows a sleek, extensible architecture: 🏛️

```
platforms/
├── base.py                # Abstract base classes
├── codechef/              # CodeChef implementation
│   ├── client.py          # HTTP client
│   └── service.py         # Business logic
├── codeforces/            # Codeforces implementation
├── geeksforgeeks/         # GeeksForGeeks implementation
├── hackerrank/            # HackerRank implementation
└── leetcode/              # LeetCode implementation
```

## 🧩 Base Classes (`base.py`)

Everything starts with our super-powered abstract base classes! 💪

### `BasePlatformClient`

```python
class BasePlatformClient(ABC):
    """Base class for platform API clients"""
    # ...
```

This class handles:
- 🔄 **Rate Limiting**: Smart throttling to avoid getting blocked
- 🌐 **HTTP Requests**: Async request handling with retries
- ⚠️ **Error Management**: Consistent error handling

### `BasePlatformService`

```python
class BasePlatformService(ABC):
    """Base class for platform services"""
    # ...
```

This class handles:
- 🔍 **Data Retrieval**: Getting user data from platforms
- ✅ **Verification**: Checking if users exist
- 📦 **Batch Processing**: Processing multiple participants

## 🍽️ Platform Implementations

### 👨‍🍳 CodeChef (`codechef/`)

The spiciest platform of them all! 🌶️

```python
class CodeChefService(BasePlatformService):
    async def get_participant_data(self, participant: Participant) -> PlatformStatus:
        # Cooking up some tasty CodeChef data...
```

### 💪 Codeforces (`codeforces/`)

For those who like to flex their algorithmic muscles! 🏋️‍♂️

### 🧠 GeeksForGeeks (`geeksforgeeks/`)

For the true geeks among us! 🤓

### 💻 HackerRank (`hackerrank/`)

Hacking the ranks, one challenge at a time! 👩‍💻

### ⚔️ LeetCode (`leetcode/`)

For the elite coders who want to conquer the coding interview! 🏆

## 🚀 How to Add a New Platform

Want to add support for a new platform? Here's how:

1. 📁 **Create a directory**: `platforms/new_platform/`
2. 🤖 **Implement a client**: `new_platform/client.py`
   ```python
   class NewPlatformClient(BasePlatformClient):
       # Implement required methods
   ```
3. 🛠️ **Implement a service**: `new_platform/service.py`
   ```python
   class NewPlatformService(BasePlatformService):
       # Implement required methods
   ```
4. 🔢 **Add to constants**: In `core/constants.py`
   ```python
   class Platform(Enum):
       # ... existing platforms
       NEW_PLATFORM = "NewPlatform"
   ```
5. 🧪 **Test it**: Using `test.py` to verify it works

## 🔍 How to Use

```python
# Create a service
service = CodeChefService()

# Get data for a single participant
status = await service.get_participant_data(participant)

# Process a batch of participants
updated_participants = await service.process_batch(participants)

# Don't forget to close when done!
await service.close()
```

## 🧪 Pro Tips

- 🕒 **Rate Limiting**: Be respectful of platforms' rate limits!
- 🔄 **Retries**: The base client has built-in retries for transient failures
- 🚫 **Error Handling**: Catch `RateLimitError` and `UserNotFoundError` for graceful handling
- 🔒 **Authentication**: Some platforms need authentication - check the specific implementation

---

Remember: With great scraping power comes great responsibility! Use these tools ethically and follow each platform's terms of service. 🦸‍♀️ 