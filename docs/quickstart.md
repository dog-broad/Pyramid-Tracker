# 🚀 Quick Start Guide

> Ready to start tracking those coding warriors? Let's get you up and running in 5 minutes! ⚡

## 🎯 Prerequisites

Make sure you have:
- ✅ Installed Pyramid-Tracker ([Installation Guide](./installation.md))
- ✅ Set up your configuration ([Configuration Guide](./configuration.md))
- ✅ A CSV file with participant details
- ✅ Your coffee ☕ (optional but recommended!)

## 🏃‍♂️ Quick Start Steps

### 1️⃣ Set Up Your Environment

```bash
# Activate your virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Check if everything is working
python main.py --help
```

### 2️⃣ Upload Your Participants

```bash
# Upload participants from your CSV
python main.py upload-users --college CMRIT --batch _2025
```

This command will:
- 📥 Read your CSV file
- 🧹 Clean up the data
- 💾 Store it in MongoDB

### 3️⃣ Verify Your Data

```bash
# Make sure all participants were uploaded correctly
python main.py verify-users --college CMRIT --batch _2025
```

### 4️⃣ Start Scraping!

```bash
# Scrape data from a single platform
python main.py scrape --college CMRIT --batch _2025 --platform CODECHEF

# Or scrape from multiple platforms at once!
python main.py multi-scrape --college CMRIT --batch _2025 --platforms CODECHEF CODEFORCES
```

## 🎮 Test Mode

Want to try things out first? Use test mode:

```bash
# Test with a small sample of participants
python main.py scrape --college CMRIT --batch _2025 --platform CODECHEF --test --sample 5
```

## 📊 Check Your Results

Your data is now in MongoDB! Each participant's record includes:
- 🏷️ Basic info (name, hall ticket number)
- 🌐 Platform handles
- 📈 Ratings and performance metrics
- 🕒 Last updated timestamps

## 🎉 What's Next?

Now that you're up and running:
- 📚 Explore the [CLI Reference](./cli.md) for more commands
- 🔧 Learn about [System Design](./architecture.md)
- 🤝 Consider [Contributing](./contributing.md)

## 🆘 Need Help?

- Check the logs for any issues
- Make sure your `.env` file is configured correctly
- Join our community for support!

Happy tracking! 🎯 