from typing import Dict, Any, Tuple, Optional

def extract_leetcode_rating(data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    """Extract LeetCode rating from API response
    
    Args:
        data (Dict[str, Any]): API response data
        
    Returns:
        Tuple[float, Dict[str, Any]]: Rating and raw data
    """
    if not data or not data.get("data") or not data.get("data", {}).get("userContestRanking"):
        return 0.0, data
    
    user_data = data["data"]["userContestRanking"]
    
    rating = user_data.get("rating", 0.0)
    if not isinstance(rating, (int, float)):
        rating = 0.0
    
    return float(rating), data

def format_graphql_query(username: str) -> str:
    """Format the GraphQL query for LeetCode API
    
    Args:
        username (str): LeetCode username
        
    Returns:
        str: Formatted GraphQL query
    """
    # Format a compact query with no unnecessary whitespace for URL encoding
    query = 'query{userContestRanking(username:"%s"){attendedContestsCount,rating,globalRanking,totalParticipants,topPercentage}}'
    
    return query % username

def extract_user_info(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract additional user info from LeetCode API response
    
    Args:
        data (Dict[str, Any]): API response data
        
    Returns:
        Dict[str, Any]: Extracted user info
    """
    if not data or not data.get("data") or not data.get("data", {}).get("userContestRanking"):
        return {}
    
    user_data = data["data"]["userContestRanking"]
    
    return {
        "rating": user_data.get("rating", 0.0),
        "global_ranking": user_data.get("globalRanking"),
        "total_participants": user_data.get("totalParticipants"),
        "top_percentage": user_data.get("topPercentage"),
        "attended_contests": user_data.get("attendedContestsCount", 0)
    } 