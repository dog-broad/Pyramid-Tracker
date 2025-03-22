from core.constants import Platform, College, Batch
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PlatformStatus:
    """Status for a competitive programming platform"""
    handle: str
    rating: Optional[float] = None
    exists: bool = False
    last_updated: datetime = field(default_factory=datetime.now)
    raw_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LeaderboardCache:
    """Cache for platform leaderboard data"""
    platform: Platform
    cache_id: str  # For GFG: contest_id/page, For HackerRank: contest_id
    entries: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

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
    
    def calculate_total_rating(self) -> float:
        """Calculate total rating across all platforms"""
        total = 0.0
        for platform_status in self.platforms.values():
            if platform_status and platform_status.rating is not None:
                total += platform_status.rating
                
        self.total_rating = total
        return total

@dataclass
class CollegeConfig:
    """Represents the configuration for a college"""
    name: College
    batches: Dict[Batch, str]
