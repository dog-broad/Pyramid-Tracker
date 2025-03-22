import yaml
from pathlib import Path
from typing import Dict, List, Optional
from core.constants import College, Batch

def extract_contest_id(url: str) -> str:
    """Extract the contest ID from a HackerRank contest URL.
    
    Args:
        url (str): Full HackerRank contest URL
        
    Returns:
        str: Contest ID extracted from the URL
    """
    return url.split('/')[-1]

def load_contests_config(config_path: Optional[str] = None) -> Dict:
    """Load HackerRank contests configuration from YAML.
    
    Args:
        config_path (Optional[str]): Path to the YAML config file
        
    Returns:
        Dict: Configuration data for HackerRank contests
    """
    if not config_path:
        config_path = Path(__file__).parent.parent / "core" / "contests.yaml"
    
    if not Path(config_path).exists():
        return {}
        
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def get_contest_urls_for_college_batch(
    college: College,
    batch: Batch,
    contests_config: Optional[Dict] = None
) -> List[str]:
    """Get the list of contest URLs for a specific college and batch.
    
    Args:
        college (College): College enum value
        batch (Batch): Batch enum value
        contests_config (Optional[Dict]): Pre-loaded contests configuration
        
    Returns:
        List[str]: List of contest URLs
    """
    if contests_config is None:
        contests_config = load_contests_config()
    
    college_key = college.value
    batch_key = str(batch.value)
    
    # Try to get college and batch specific contests
    if college_key in contests_config.get('hackerrank', {}).get('contests', {}):
        college_contests = contests_config['hackerrank']['contests'][college_key]
        
        # Check for batch-specific contests
        if batch_key in college_contests:
            return college_contests[batch_key]
        # Fall back to common contests for the college
        elif 'common' in college_contests:
            return college_contests['common']
    
    # Fall back to global contests
    return contests_config.get('hackerrank', {}).get('contests', {}).get('common', []) 