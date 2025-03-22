import re
from core.constants import Batch, College
from core.logging import get_logger
import pandas as pd

logger = get_logger(__name__)

BLACK_LIST = ["gmail.com", "cmritonline.ac.in"]

def remove_non_ascii(input_string: str) -> str:
    """Remove non-ASCII characters from a string."""
    return re.sub(r'[^\x00-\x7F]+', '', input_string)


def clean_handles_col(df: pd.DataFrame, handle_columns: list) -> pd.DataFrame:
    """Clean the specified handle columns in a DataFrame by removing unwanted characters."""

    for column in handle_columns:
        if column in df.columns:
            logger.info(f"Cleaning handle column: {column}")
            # Apply the `clean_handle` function to each entry in the specified column
            df[column] = df[column].apply(clean_handle)
        else:
            logger.warning(f"Column {column} not found in the DataFrame.")
    return df


def clean_handle(handle: str) -> str:
    """Clean a single handle by removing unwanted characters and ensuring standard format."""

    handle = str(handle).strip()  # Convert to string and remove leading/trailing spaces
    if is_email(handle):
        # If handle is an email, take only the part before '@'
        handle = handle.split("@")[0]
    handle = remove_non_ascii(handle)  # Remove non-ASCII characters
    handle = handle.lower()  # Convert to lowercase
    # remove blacklist words from handle
    for word in BLACK_LIST:
        handle = handle.replace(word, "")
    handle = handle.replace("@", "").replace("#N/A", "")  # Remove specific unwanted characters
    handle = handle.replace(".", "").replace(" ", "")  # Remove dots and spaces
    return handle if handle else None


def is_email(handle: str) -> bool:
    """Match string against a basic email pattern."""
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', handle)


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize the column names in a DataFrame."""
    # The current expected order of columns
    #  - Handle - 0
    #  - GeeksForGeeksHandle - 1
    #  - CodeforcesHandle - 2
    #  - LeetCodeHandle - 3
    #  - CodeChefHandle - 4
    #  - HackerRankHandle - 5
    
    # The desired column names amd the order they should be in
    # - HallTicketNo - 0
    # - CodeChefHandle - 4
    # - CodeforcesHandle - 2
    # - GeeksForGeeksHandle - 1
    # - LeetCodeHandle - 3
    # - HackerRankHandle - 5
    
    # We cant compare names, but we can compare indices
    expected_column_indices = [0, 4, 2, 1, 3, 5]
    current_column_indices = df.columns.map(df.columns.get_loc).tolist()
    if current_column_indices != expected_column_indices:
        df = df.iloc[:, expected_column_indices]

    df.columns = ["HallTicketNo", "CodeChefHandle", "CodeforcesHandle", "GeeksForGeeksHandle", "LeetCodeHandle", "HackerRankHandle"]
    return df