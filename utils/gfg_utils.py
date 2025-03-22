from typing import Dict, Any, Tuple, Optional

def calculate_gfg_rating(weekly_rating: float, practice_rating: float, weekly_weight: float = 0.75) -> float:
    """Calculate the weighted GeeksforGeeks rating using weekly contest and practice scores.
    
    Args:
        weekly_rating (float): Rating from weekly contests
        practice_rating (float): Rating from practice problems
        weekly_weight (float): Weight to give to weekly contest scores (default: 0.75)
        
    Returns:
        float: Weighted combined rating
    """
    # Ensure ratings are not None
    weekly_rating = weekly_rating or 0.0
    practice_rating = practice_rating or 0.0
    
    # Calculate weighted rating
    return (weekly_rating * weekly_weight) + (practice_rating * (1 - weekly_weight))

def extract_practice_score(api_response: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    """Extract practice score from the GeeksforGeeks API response.
    
    Args:
        api_response (Dict[str, Any]): API response from GFG profile API
        
    Returns:
        Tuple[float, Dict[str, Any]]: Practice score and raw data
    """
    try:
        if not api_response:
            return 0.0, {}
            
        # Extract score from data field
        score = api_response.get('data', {}).get('score', 0)
        
        # Handle None or non-numeric values
        if score is None or not isinstance(score, (int, float)):
            score = 0.0
            
        return float(score), api_response
    except Exception:
        return 0.0, api_response or {}

def extract_weekly_contest_score(leaderboard_entries: Dict[str, Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
    """Extract and aggregate weekly contest scores.
    
    Args:
        leaderboard_entries (Dict[str, Dict[str, Any]]): Dictionary of leaderboard entries keyed by contest ID
        
    Returns:
        Tuple[float, Dict[str, Any]]: Total weekly contest score and raw data
    """
    if not leaderboard_entries:
        return 0.0, {}
        
    total_score = 0.0
    
    for contest_id, entry in leaderboard_entries.items():
        score = entry.get('user_score', 0)
        if score is not None and isinstance(score, (int, float)):
            total_score += float(score)
    
    return total_score, leaderboard_entries 