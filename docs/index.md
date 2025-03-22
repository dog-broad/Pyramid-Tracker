# 📚 Pyramid-Tracker Documentation 

> Welcome to the epic documentation of Pyramid-Tracker! 🎉 Find everything you need to know about our awesome competitive programming tracking system.

## 📖 Contents

### 🚀 Getting Started
- [Installation Guide](./installation.md) - Get up and running in no time! ⏱️
- [Configuration Guide](./configuration.md) - Set up your environment just right ⚙️
- [Quick Start Tutorial](./quickstart.md) - Your first tracking session in 5 minutes! 🏎️

### 🧩 Core Modules
- [Core Module](./core.md) - The brain of our operation! 🧠
- [Database Module](./database.md) - Where our data lives and breathes 🗃️
- [Platforms Module](./platforms.md) - Connect to coding platforms galore! 🌐
- [Scripts Module](./scripts.md) - Handy utilities to make life easier 🛠️
- [Utils Module](./utils.md) - Small but mighty helper functions 🧰

### 🧙‍♂️ CLI Reference
- [Command Line Interface](./cli.md) - Master the terminal commands 💻

### 🏗️ Architecture
- [System Design](./architecture.md) - How all the pieces fit together 🧩

### 👨‍💻 Contributing
- [Developer Guide](./contributing.md) - Join our awesome team of contributors! 👨‍💻

## 🔍 Quick Reference

### Common Tasks

```bash
# Upload participants from a CSV
python main.py upload-users --college CMRIT --batch _2025

# Scrape CodeChef data
python main.py scrape --college CMRIT --batch _2025 --platform CODECHEF

# Run test mode with multiple platforms
python main.py --college CMRIT --batch _2025 --test --platforms codechef codeforces
```

### Common Imports

```python
# Core components
from core.constants import Platform, Batch, College
from core.logging import get_logger
from core.config import get_settings

# Database operations
from db.client import DatabaseClient
from db.repositories import ParticipantRepository

# Platform services
from platforms.codechef import CodeChefService
# ... and more!
```

## 🚀 Need Help?

Don't panic! If you get stuck, here's what to do:

1. Check the logs - they're super informative! 🔍
2. Look for error messages - they'll point you in the right direction 🧭
3. Read the relevant documentation section again 📖
4. Still stuck? Reach out to the team! We don't bite! 🦈 (well, maybe a little)

---

Made with ❤️ and a healthy dose of caffeine ☕ by the Pyramid Team 