# 🔥 Pyramid-Tracker 🔥

> Keeping track of your coding warriors across multiple competitive programming platforms! 🚀

## 🌟 What is This?

Pyramid-Tracker is a super cool tool that scrapes data from various competitive programming platforms (CodeChef, Codeforces, HackerRank, GeeksForGeeks, LeetCode) to track the performance of participants (like students in a college batch). It's the perfect tool for teachers, mentors, and team leads who want to keep an eye on how their coding warriors are performing! 💪

## 🛠️ Features

- 🤖 **Multi-Platform Support**: Tracks user data across 5 competitive programming platforms
- 🔄 **Asynchronous Scraping**: Fast, efficient data collection with smart rate limiting
- 🗃️ **MongoDB Integration**: Store and retrieve participant data with ease
- 📊 **Batch Processing**: Manage participants by college and graduation batch
- 🧙‍♂️ **Command-Line Interface**: Simple commands to control everything
- 🚦 **Robust Error Handling**: Gracefully handles rate limits and network issues

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- MongoDB
- A good sense of humor 😉

### Installation

1. Clone this repo:
   ```
   git clone https://your-repo-url/Pyramid-Tracker.git
   cd Pyramid-Tracker
   ```

2. Set up your virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create your `.env` file (see `.env.example` for a template)

5. Run the application:
   ```
   python main.py --help
   ```

## 🧩 How It Works

Our architecture is as awesome as a perfectly balanced binary tree! 🌳

1. **Core Components**: Constants, configurations, and exceptions that power everything
2. **Platform Services**: Services for each competitive programming platform
3. **Database Layer**: MongoDB client and repositories for data management
4. **CLI Interface**: Easy-to-use commands to make magic happen

## 🔧 Usage Examples

### Upload Participants

```bash
python main.py upload-users --college CMRIT --batch _2025
```

### Scrape Platform Data

```bash
python main.py scrape --college CMRIT --batch _2025 --platform CODECHEF
```

### Run with Test Mode

```bash
python test.py --college CMRIT --batch _2025 --test --platforms codechef codeforces
```

## 🧐 Architecture Overview

```
Pyramid-Tracker/
├── core/                 # Core functionality and configurations
├── db/                   # Database models and repositories
├── platforms/            # Platform-specific implementations
│   ├── base.py           # Base abstract classes
│   ├── codechef/         # CodeChef implementation
│   ├── codeforces/       # Codeforces implementation
│   └── ...               # Other platforms
├── scripts/              # Utility scripts
├── services/             # Business logic services
├── utils/                # Helper utilities
├── main.py               # CLI entry point
└── test.py               # Test script for development
```

## 💡 Contributing

Got ideas to make this even more awesome? We're all ears! 👂

1. Fork the repo
2. Create a feature branch: `git checkout -b cool-new-feature`
3. Commit your changes: `git commit -am 'Add some coolness'`
4. Push to the branch: `git push origin cool-new-feature`
5. Submit a pull request ✨

## 🤔 Troubleshooting

- **Rate Limiting**: If you hit rate limits, the application will automatically wait and retry. Be patient! ⏳
- **MongoDB Connection**: Make sure your MongoDB connection string in `.env` is correct
- **Platform API Changes**: If a platform changes its API, check the corresponding platform service implementation

## 🎯 Future Enhancements

- Web dashboard for visualizing data 📊
- Email notifications for rating changes 📧
- Support for more competitive programming platforms 🌐
- Performance analytics and recommendations 📈

---

Made with ❤️ by the Pyramid Team 