"""
This file contains constants used throughout the application.

Standards:

- Platform constants should be in all uppercase and separated by underscores.
- College constants should be in all uppercase and separated by underscores.
- Batch constants should be in the format of _YYYY, where YYYY is the year of graduation.

Example:

class Platform(Enum):
    ...
    # GitHub
    GITHUB = "github"

class College(Enum):
    ...
    # CMR University
    CMRU = "CMR University"

class Batch(Enum):
    ...
    # 2028 batch
    _2028 = "2028"

"""
from enum import Enum

class Platform(Enum):
    CODECHEF = "CodeChef"
    CODEFORCES = "Codeforces"
    GEEKSFORGEEKS = "GeeksforGeeks"
    HACKERRANK = "HackerRank"
    LEETCODE = "LeetCode"
    
class College(Enum):
    CMRIT = "CMR Institute of Technology"

class Batch(Enum):
    _2025 = 2025
    _2026 = 2026
    _2027 = 2027

