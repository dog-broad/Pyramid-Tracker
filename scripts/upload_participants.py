import os
import json
import shutil
import subprocess
import sys
import typing as t

import pandas as pd
import yaml

from core.config import get_settings
from core.constants import Batch, College
from core.logging import get_logger

from db.client import DatabaseClient
from db.models import CollegeConfig
from db.repositories import ParticipantRepository

from utils.df_utils import clean_handles_col, standardize_column_names

settings = get_settings()
logger = get_logger(__name__)

def sheet_download_if_not_exists(file_path, url):
    """Download a sheet from a URL if it doesn't exist locally"""
    if not os.path.exists(file_path):
        logger.info(f"File {file_path} does not exist. Downloading the sheet.")
        
        # If data folder is not present, create it
        if not os.path.exists("data"):
            os.makedirs("data")

        # Construct the download command based on the OS
        if os.name.lower() == 'nt':
            # Windows command using PowerShell
            command = ['curl', '-L', url, '-o', file_path]
        else:
            # Non-Windows command using wget or curl
            if shutil.which('wget'):  # Check if wget is available
                command = ['wget', url, '-O', file_path]
            else:
                # Fall back to curl if wget is not available
                command = ['curl', '-L', url, '-o', file_path]

        # Execute the command
        try:
            result = subprocess.run(command, check=True, text=True)
            logger.info("Command executed successfully. Downloaded the sheet.")
        except subprocess.CalledProcessError as e:
            logger.error("Error occurred during download.", exc_info=True)
            logger.error(f"Error output: {e.stderr}")
            raise
        
# Function to convert YAML data into CollegeConfig instances
def parse_college_config(data: dict) -> t.List[CollegeConfig]:
    logger.info("Parsing YAML data into CollegeConfig instances")
    colleges = []
    for college_name, college_data in data['colleges'].items():
        batches = {
            int(batch_year): urls
            for batch_year, urls in college_data['batches'].items()
        }
        college_config = CollegeConfig(name=college_name, batches=batches)
        colleges.append(college_config)
    return colleges

def upload_participants(college_name: str, batch_name: str) -> None:
    # The college and batch names are passed as command-line arguments,
    # which are already locked into the Enum values within core.constants
    #
    # That's why it is safe to assume that these values are valid
    try:
        college = College[college_name]
        batch = Batch[batch_name]

        logger.info(f"Uploading users for {college} {batch}")

        with open("core/user_details.yaml", "r") as f:
            user_details = yaml.safe_load(f)

        colleges = parse_college_config(user_details)
        college_config = next(c for c in colleges if c.name == college.name)

        batch_url = college_config.batches.get(batch.value)[0]

        if not batch_url:
            raise ValueError(f"Batch URL not found for {college.name} {batch.name}")
        
        sheet_download_if_not_exists(f"data/{college.name}{batch.name}.csv", batch_url)

        df = pd.read_csv(f"data/{college.name}{batch.name}.csv")

        df = clean_handles_col(df, handle_columns=df.columns[1:])
        df = standardize_column_names(df)
        
        db_client = DatabaseClient(college.name)
        repo = ParticipantRepository(db_client)

        # Replace actual NaN values with an empty string
        df.fillna("", inplace=True)

        # Replace string "nan" (which might be in the dataset) with an empty string
        df.replace("nan", "", inplace=True)

        # Export to CSV
        df.to_csv(f"data/{college.name}{batch.name}_cleaned.csv", index=False)

        
        # add a column Batch to the dataframe
        df["Batch"] = batch

        # add a column College to the dataframe
        df["College"] = college
        
        # Set all values of batch and college to the same value
        df["Batch"] = batch.value
        df["College"] = college.value
        
        repo.bulk_upload_from_dataframe(df, batch, college)
    except Exception as e:
        logger.error("Error uploading users", error=str(e), exc_info=True)

