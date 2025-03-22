# 📁 Configuration Guide

> Pyramid-Tracker requires configuration for logging, database access, API credentials, and URLs. All configuration values are set in a `.env` file. You can customize these settings to suit your environment.

## 🌍 Overview

Pyramid-Tracker requires configuration for logging, database access, API credentials, and URLs. All configuration values are set in a `.env` file. You can customize these settings to suit your environment.

### 📜 Steps to Configure

1. **Copy the `.env.example` File**  
   To get started, copy the `.env.example` file to `.env` in the root directory of the Pyramid-Tracker project:
   ```bash
   cp .env.example .env
   ```
   This will create a new `.env` file with default values that you can modify.

2. **Edit the `.env` File**  
   Open the `.env` file in a text editor and fill in the required values. Here's a breakdown of each section.

---

## 📝 Configuration Breakdown

### 1. **Logging Settings**  
   Controls the verbosity of logging for debugging purposes.

   - `LOG_DEBUG=false`  
     Set to `true` for detailed logging output. Recommended for debugging.

---

### 2. **Database Settings**  
   Configure the connection to the MongoDB database.

   - `DB_MONGODB_URI=mongodb://localhost:27017/`  
     URL of your MongoDB instance.
   
   - `DB_MONGODB_PASSWORD=your_mongodb_password`  
     Set this to the password used to connect to MongoDB.

---

### 3. **API Credentials**  
   Set your API keys and secrets for the various platforms supported by Pyramid-Tracker.

   #### CodeChef
   - `API_CODECHEF_CLIENT_ID=your_codechef_client_id`  
   - `API_CODECHEF_CLIENT_SECRET=your_codechef_client_secret`  

   #### Codeforces
   - `API_CODEFORCES_KEY=your_codeforces_key`  
   - `API_CODEFORCES_SECRET=your_codeforces_secret`  

   #### GeeksForGeeks
   - `API_GFG_USERNAME=your_gfg_username`  
     Your username for GeeksForGeeks. (Not required in the current implementation)
   - `API_GFG_PASSWORD=your_gfg_password`  
     Your password for GeeksForGeeks. (Not required in the current implementation)

   #### GitHub (Optional)
   - `API_GIT_USERNAME=your_github_username`  
     Your GitHub username. (Not required in the current implementation)
   - `API_GIT_PASSWORD=your_github_personal_access_token`  
     A GitHub personal access token for API access. (Not required in the current implementation)

---

### 4. **URL Settings**  
   These URLs point to the relevant API endpoints for each platform.

   #### CodeChef
   - `URL_CODECHEF_API_URL=https://api.codechef.com/`  
     The base URL for CodeChef API.
   - `URL_CODECHEF_URL=https://www.codechef.com/`  
     The main website URL.

   #### Codeforces
   - `URL_CODEFORCES_URL=https://codeforces.com/`  
     The main website URL for Codeforces.

   #### GeeksForGeeks
   - `URL_GEEKSFORGEEKS_URL=https://www.geeksforgeeks.org/`  
     The main website URL for GeeksForGeeks.
   - `URL_GFG_API_URL=https://practiceapi.geeksforgeeks.org/api/`  
     The API URL for GeeksForGeeks.
   - `URL_GFG_PRACTICE_URL=https://practice.geeksforgeeks.org/`  
     The practice problems URL.
   - `URL_GFG_WEEKLY_CONTEST_URL=https://practiceapi.geeksforgeeks.org/api/v1/get-user-contests`  
     The URL for fetching weekly contests.

   #### HackerRank
   - `URL_HACKERRANK_API_URL=https://www.hackerrank.com/rest/`  
     The API URL for HackerRank.
   - `URL_HACKERRANK_URL=https://www.hackerrank.com/`  
     The main website URL for HackerRank.

   #### LeetCode
   - `URL_LEETCODE_URL=https://leetcode.com/`  
     The main website URL for LeetCode.

---

## 🔑 Example `.env` Configuration

Please refer to the `.env.example` file for the expected format and values.

---

## 🚨 Troubleshooting

If you encounter any issues, here are some common problems and solutions:

- **Error: "Database connection failed"**  
   Solution: Check your `DB_MONGODB_URI` and `DB_MONGODB_PASSWORD` settings.
   
- **Error: "API Key Invalid"**  
   Solution: Verify that your API credentials for CodeChef, Codeforces, or any other platform are correct.

- **Error: "URL not accessible"**  
   Solution: Double-check the URLs for each platform in your `.env` file.
