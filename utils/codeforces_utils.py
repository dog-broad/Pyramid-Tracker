import random
import string
import hashlib
from typing import Optional, Union

def generate_random_string(length: int) -> str:
    """Generate a random string of specified length.
    
    Args:
        length (int): Length of the random string to generate.
        
    Returns:
        str: A random string composed of lowercase letters and digits.
    """
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_api_sig(
    random_string: str, 
    method_name: str, 
    handle_string: str, 
    current_time: int, 
    secret: str, 
    api_key: str
) -> str:
    """Generate an API signature for Codeforces API requests.
    
    Args:
        random_string (str): A random string to use in the signature.
        method_name (str): The Codeforces API method being called.
        handle_string (str): The handle(s) being queried, joined by semicolons.
        current_time (int): Current Unix timestamp.
        secret (str): Your Codeforces API secret.
        api_key (str): Your Codeforces API key.
        
    Returns:
        str: A SHA512 hexadecimal digest for the API request.
    """
    # Create the string to hash according to Codeforces API rules
    # Format: random_string/method.name?param1=value1&param2=value2...#secret
    to_hash = f"{random_string}/{method_name}?apiKey={api_key}&handles={handle_string}&time={current_time}#{secret}"
    
    # Calculate SHA512 hash
    return hashlib.sha512(to_hash.encode('utf-8')).hexdigest() 