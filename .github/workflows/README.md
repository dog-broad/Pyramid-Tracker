# Pyramid-Tracker GitHub Workflows

This directory contains GitHub Actions workflows for automating various tasks in the Pyramid-Tracker project.

## Workflow Overview

### 1. Weekly Data Pipeline (`weekly-data-pipeline.yml`)
- **Purpose**: Runs the complete data pipeline (scraping, evaluation, leaderboard generation) on a weekly schedule.
- **Schedule**: Runs automatically at 00:00 every Sunday.
- **Manual Trigger**: Can be triggered manually with custom parameters.
- **Parameters**:
  - `college`: College to process (dropdown selection)
  - `batch`: Batch to process (dropdown selection)
  - `platforms`: Platform names to scrape (dropdown selection with options)
  - `debug`: Enable debug mode with verbose logging
- **Example**:
  - To run for CMRIT 2025 students on all platforms:
    - College: `CMRIT`
    - Batch: `_2025`
    - Platforms: `ALL`

### 2. Platform Scrape (`platform-scrape.yml`)
- **Purpose**: Scrapes data from a specific platform.
- **Parameters**:
  - `college`: College to process (dropdown selection)
  - `batch`: Batch to process (dropdown selection)
  - `platform`: Single platform to scrape (dropdown selection)
  - `test`: Run in test mode with limited participants
  - `sample`: Number of participants to select in test mode
  - `debug`: Enable debug mode
- **Example**:
  - To scrape CodeChef data for CMRIT 2025:
    - College: `CMRIT`
    - Batch: `_2025`
    - Platform: `CODECHEF`

### 3. Multi-Platform Scrape (`multi-platform-scrape.yml`)
- **Purpose**: Scrapes data from multiple platforms.
- **Parameters**:
  - `college`: College to process (dropdown selection)
  - `batch`: Batch to process (dropdown selection)
  - `platforms`: Platforms to scrape (dropdown with predefined combinations)
  - `test`: Run in test mode with limited participants
  - `sample`: Number of participants to select in test mode
  - `debug`: Enable debug mode
- **Example**:
  - To scrape LeetCode and Codeforces data:
    - Platforms: `CODEFORCES LEETCODE`

### 4. Manage Participants (`manage-participants.yml`)
- **Purpose**: Upload or verify participants.
- **Parameters**:
  - `action`: Action to perform (`upload` or `verify`)
  - `college`: College to process (dropdown selection)
  - `batch`: Batch to process (dropdown selection)
  - `debug`: Enable debug mode
- **Example**:
  - To verify participants for CMRIT 2025:
    - Action: `verify`
    - College: `CMRIT`
    - Batch: `_2025`

### 5. Evaluation and Leaderboard (`evaluation.yml`)
- **Purpose**: Evaluate participants and/or generate leaderboards.
- **Parameters**:
  - `college`: College to process (dropdown selection)
  - `batch`: Batch to process (dropdown selection)
  - `action`: Action to perform (`evaluate`, `leaderboard`, or `both`)
  - `output`: Output file name for leaderboard
  - `charts`: Include charts in leaderboard
  - `debug`: Enable debug mode
- **Example**:
  - To evaluate and generate leaderboards:
    - Action: `both`
    - College: `CMRIT` 
    - Batch: `_2025`

## Common Parameters

- **college**: Based on the `College` enum in `core/constants.py` (available as dropdown in the workflow interface)
- **batch**: Based on the `Batch` enum in `core/constants.py` (available as dropdown in the workflow interface)
- **platforms**: Based on the `Platform` enum in `core/constants.py` (available as dropdown in the workflow interface)
- **debug**: Enable debug mode with verbose logging (default: `false`)
- **test**: Run in test mode with limited participants (default: `false`)
- **sample**: Number of participants to select in test mode (default: `20`)

## Required Secrets

The following secrets must be configured in the GitHub repository:

- `MONGODB_URI`: MongoDB connection URI
- `MONGODB_PASSWORD`: MongoDB password
- `API_CODEFORCES_KEY`: Codeforces API key
- `API_CODEFORCES_SECRET`: Codeforces API secret
- `API_CODECHEF_CLIENT_ID`: CodeChef API client ID
- `API_CODECHEF_CLIENT_SECRET`: CodeChef API client secret
- `API_GFG_USERNAME`: GeeksforGeeks username
- `API_GFG_PASSWORD`: GeeksforGeeks password

## Adding New Workflows

When adding new workflows:

1. Use the reusable actions in `reusable-actions.yml` where possible
2. Follow the existing naming conventions
3. Document the workflow in this README
4. Ensure that logs and artifacts are properly uploaded

## Notes

- The application is designed to connect to a remote MongoDB server, so there's no local MongoDB setup in the workflows.
- All inputs are provided as dropdown selections where possible to make running workflows easier.
- Workflows can be run directly from the GitHub Actions tab in the repository.