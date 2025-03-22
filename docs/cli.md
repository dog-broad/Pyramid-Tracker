# 💻 Command Line Interface Guide

> Master the art of commanding Pyramid-Tracker! 🎮 Here's your complete guide to all CLI commands.

## 🚀 Basic Usage

```bash
# Get help on available commands
python main.py --help

# Enable debug mode
python main.py --debug [command]

# Run with logging to a file
python main.py --log-file run_log.log [command]
```

## 📋 Available Commands

### 📤 Upload Users

Upload participants from CSV files to the database.

```bash
python main.py upload-users --college CMRIT --batch _2025
```

Options:
- 🏫 `--college`: College name (e.g., CMRIT)
- 📅 `--batch`: Batch year (e.g., _2025)

### ✅ Verify Users

Check if users exist in the database.

```bash
python main.py verify-users --college CMRIT --batch _2025
```

Options:
- 🏫 `--college`: College name
- 📅 `--batch`: Batch year

### 🕸️ Scrape Data

Scrape data from a specific platform.

```bash
python main.py scrape --college CMRIT --batch _2025 --platform CODECHEF [--test] [--sample 5]
```

Options:
- 🏫 `--college`: College name
- 📅 `--batch`: Batch year
- 🌐 `--platform`: Platform name (CODECHEF, CODEFORCES, etc.)
- 🧪 `--test`: Enable test mode
- 📊 `--sample`: Number of participants to test with (default: 20)

### 🔄 Multi-Platform Scrape

Scrape data from multiple platforms at once.

```bash
python main.py multi-scrape --college CMRIT --batch _2025 --platforms CODECHEF CODEFORCES
```

Options:
- 🏫 `--college`: College name
- 📅 `--batch`: Batch year
- 🌐 `--platforms`: One or more platforms (or ALL)
- 🧪 `--test`: Enable test mode
- 📊 `--sample`: Sample size for test mode

### 📊 Evaluate Participants

Evaluate participant performance across platforms.

```bash
python main.py evaluate --college CMRIT --batch _2025
```

Options:
- 🏫 `--college`: College name
- 📅 `--batch`: Batch year

### 🏆 Generate Leaderboard

Generate a leaderboard for participants.

```bash
python main.py generate-leaderboard --college CMRIT --batch _2025 --output leaderboard.xlsx
```

Options:
- 🏫 `--college`: College name
- 📅 `--batch`: Batch year
- 📂 `--output`: Output file path (default: leaderboard.xlsx)
- 📈 `--charts`: Include charts in the leaderboard (default: True)

### 🚀 Run Complete Pipeline

Run the complete Pyramid-Tracker pipeline.

```bash
python main.py run-pipeline --college CMRIT --batch _2025 --platforms ALL --output leaderboard.xlsx
```

Options:
- 🏫 `--college`: College name
- 📅 `--batch`: Batch year
- 🌐 `--platforms`: One or more platforms (or ALL)
- 📂 `--output`: Output leaderboard file path (default: leaderboard.xlsx)
- 📈 `--charts`: Include charts in the leaderboard (default: True)
- 🧪 `--test`: Enable test mode
- 📊 `--sample`: Number of random participants to select in test mode (default: 20)

## 🎯 Examples

### 1️⃣ Basic Data Upload

```bash
# Upload new batch of participants
python main.py upload-users --college CMRIT --batch _2025
```

### 2️⃣ Test Mode Scraping

```bash
# Test scraping with 5 participants
python main.py scrape --college CMRIT --batch _2025 --platform CODECHEF --test --sample 5
```

### 3️⃣ Multi-Platform Scraping

```bash
# Scrape from all platforms
python main.py multi-scrape --college CMRIT --batch _2025 --platforms ALL

# Scrape from specific platforms
python main.py multi-scrape --college CMRIT --batch _2025 --platforms CODECHEF LEETCODE
```

### 4️⃣ Generate Leaderboard

```bash
# Generate leaderboard with charts
python main.py generate-leaderboard --college CMRIT --batch _2025 --output leaderboard.xlsx --charts
```

### 5️⃣ Run Complete Pipeline

```bash
# Run complete pipeline with test mode
python main.py run-pipeline --college CMRIT --batch _2025 --platforms ALL --output leaderboard.xlsx --test --sample 10
```

## 🎮 Command Structure

All commands follow this general structure:
```bash
python main.py [--debug] <command> <required-options> [optional-options]
```

## � Logging Options

The CLI provides flexible logging options to help you monitor and debug operations:

### Debug Mode
Enable verbose logging for detailed insights into the command execution:
```bash
python main.py --debug scrape --college CMRIT --batch _2025 --platform CODECHEF
```

### Custom Log File
Specify a custom log file path to store logs:
```bash
python main.py --log-file custom_log.log scrape --college CMRIT --batch _2025 --platform CODECHEF
```

### Combined Usage
You can combine both debug mode and custom log file:
```bash
python main.py --debug --log-file debug_log.log scrape --college CMRIT --batch _2025 --platform CODECHEF
```

## 🚦 Exit Codes

- ✅ **0**: Success
- ❌ **1**: General error
- 🔒 **2**: Authentication error
- 🌐 **3**: Network error
- 💾 **4**: Database error

## � Running in Background

For long-running operations:

```bash
# Linux/Mac
nohup python main.py scrape --college CMRIT --batch _2025 --platform CODECHEF &

# Windows (PowerShell)
Start-Process python -ArgumentList "main.py scrape --college CMRIT --batch _2025 --platform CODECHEF"
```

## 🔧 Environment Variables

The CLI respects these environment variables:
- 📝 `LOG_DEBUG`: Enable debug logging
- 🗃️ `DB_MONGODB_URI`: MongoDB connection string
- 🔑 `API_*`: Various API credentials

## 🆘 Common Issues

### 1️⃣ Command Not Found
```bash
# Make sure you're in the right directory
cd /path/to/Pyramid-Tracker
```

### 2️⃣ Permission Errors
```bash
# Check if virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 3️⃣ Database Connection
```bash
# Verify MongoDB is running
mongod --version
```

## 🎯 Pro Tips

1. 📝 **Use Tab Completion**
   ```bash
   # Install argcomplete for tab completion
   pip install argcomplete
   ```

2. 🔄 **Chain Commands**
   ```bash
   # Upload and verify in one go
   python main.py upload-users --college CMRIT --batch _2025 && python main.py verify-users --college CMRIT --batch _2025
   ```

3. 📊 **Monitor Progress**
   ```bash
   # Enable debug mode for detailed progress
   python main.py --debug scrape --college CMRIT --batch _2025 --platform CODECHEF
   ```

---

Remember: The CLI is your friend! 🤝 It's designed to make your life easier, not harder!