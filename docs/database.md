# 🗃️ Database Module Documentation

> Where all our precious data lives! 💎 This module handles all database interactions in Pyramid-Tracker.

## 📊 Overview

The database module is the backbone of our application, storing and retrieving participant information with MongoDB. Think of it as our treasure vault! 🏦

```
db/
├── client.py          # MongoDB connection management
├── models.py          # Data models and types
└── repositories.py    # Data access logic
```

## 🧬 Models (`models.py`)

Our data models are like DNA - they define what our data looks like! 🧪

### `PlatformStatus`

```python
@dataclass
class PlatformStatus:
    """Status for a competitive programming platform"""
    handle: str
    rating: Optional[float] = None
    exists: bool = False
    last_updated: datetime = field(default_factory=datetime.now)
    raw_data: Dict[str, Any] = field(default_factory=dict)
```

Stores a participant's status on a specific platform:
- 🏷️ **handle**: Username on the platform
- 🔢 **rating**: Numerical rating (if available)
- ✅ **exists**: Whether the user exists on the platform
- 🕒 **last_updated**: When the data was last refreshed
- 📄 **raw_data**: Any additional platform-specific data

### `Participant`

```python
@dataclass
class Participant:
    """Represents a participant with their platform statuses"""
    hall_ticket_no: str
    name: str
    batch: Batch
    college: College
    platforms: Dict[Platform, Optional[PlatformStatus]] = field(default_factory=dict)
    total_rating: float = 0.0
    percentile: float = 0.0
```

The main star of our show! Represents a person being tracked:
- 🆔 **hall_ticket_no**: Unique identifier
- 👤 **name**: Human-readable name
- 🎓 **batch**: Graduation year
- 🏫 **college**: Educational institution
- 🌐 **platforms**: Status on different coding platforms
- 📈 **total_rating**: Combined score across platforms
- 📊 **percentile**: Relative standing in the batch

## 🔌 Database Client (`client.py`)

The `DatabaseClient` class is our personal assistant for MongoDB! 🧙‍♀️

```python
class DatabaseClient:
    """MongoDB client wrapper with connection pooling"""
    # ...
```

Key features:
- 🔄 **Connection Pooling**: Efficient reuse of database connections
- 🧠 **Singleton Pattern**: Only one client instance for the application
- 🛡️ **Error Handling**: Graceful handling of database errors

## 📚 Repositories (`repositories.py`)

The `ParticipantRepository` class is like a super-organized librarian! 📚

```python
class ParticipantRepository:
    """Repository for participant data"""
    # ...
```

Key methods:
- 📥 **insert_participant**: Add a new participant
- 📤 **get_all_participants**: Retrieve all participants for a batch
- 🔄 **update_participant**: Modify an existing participant
- 🎲 **get_random_participants**: Get a random sample (useful for testing)
- 📊 **bulk_upload_from_dataframe**: Import data from pandas DataFrame

## 🔍 How to Use

```python
# Connect to the database
db_client = DatabaseClient("CMRIT")

# Create a repository for participant operations
repo = ParticipantRepository(db_client)

# Get all participants from a batch
participants = repo.get_all_participants("_2025", "CMRIT")

# Update a participant
participant.platforms[Platform.CODECHEF].rating = 1800
repo.update_participant(participant)

# Import from CSV/DataFrame
repo.bulk_upload_from_dataframe(dataframe, batch, college)
```

## 🧪 Pro Tips

- 📁 **Collection Naming**: Collections follow the pattern `{college}{batch}`
- 🔄 **Document Conversion**: Use `_document_to_participant` and `_participant_to_document` for conversions
- 📄 **Bulk Operations**: Use `update_participants` for updating multiple records efficiently
- 🧮 **Calculating Ratings**: Call `participant.calculate_total_rating()` to refresh the total score

## 🏗️ Schema Design

Our MongoDB collections use a document structure that mirrors our `Participant` class:

```json
{
  "hallTicketNo": "1234",
  "name": "John Doe",
  "batch": 2025,
  "college": "CMRIT",
  "platforms": {
    "CodeChef": {
      "handle": "johndoe42",
      "rating": 1820,
      "exists": true,
      "lastUpdated": "2023-06-15T14:23:10Z"
    },
    "Codeforces": {
      "handle": "john_doe",
      "rating": 1450,
      "exists": true,
      "lastUpdated": "2023-06-15T14:25:18Z"
    }
  },
  "totalRating": 3270,
  "percentile": 85.4
}
```

---

Remember: A clean database is a happy database! 🧹 Always validate your data before insertion and keep your queries efficient. 🚀 