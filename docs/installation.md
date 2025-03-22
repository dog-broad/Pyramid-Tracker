# 🚀 Installation Guide

> Let's get this party started! 🎉 Follow these steps to set up Pyramid-Tracker on your system.

## 📋 Prerequisites

Before we begin, make sure you have:

- 🐍 **Python 3.7+** - Our code is Pythonic, so you'll need Python!
- 🍃 **MongoDB** - Our database of choice (4.0+ recommended)
- 🧙‍♂️ **pip** - The Python package installer
- 🔄 **git** - For cloning the repository
- ☕ **Coffee** - Optional but highly recommended

## 🔽 Installation Steps

### 1️⃣ Clone the Repository

```bash
# Clone the repo
git clone https://github.com/yourusername/Pyramid-Tracker.git

# Navigate to the project directory
cd Pyramid-Tracker
```

### 2️⃣ Set Up a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

You should see `(venv)` appear at the beginning of your terminal prompt, indicating that the virtual environment is active. It's like putting on your coding superhero cape! 🦸‍♀️

### 3️⃣ Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

This will install all the magical packages we need! ✨

### 4️⃣ Set Up MongoDB

Make sure MongoDB is running on your system. If you haven't installed it yet:

- 🪟 **Windows**: [MongoDB Windows Installation](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/)
- 🍎 **macOS**: [MongoDB macOS Installation](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-os-x/)
- 🐧 **Linux**: [MongoDB Linux Installation](https://docs.mongodb.com/manual/administration/install-on-linux/)

### 5️⃣ Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Create .env file
cp .env.example .env

# Now edit the .env file with your favorite editor
# For example:
nano .env
```

Update the environment variables with your actual values:

```
# Database settings
DB_MONGODB_URI=mongodb://localhost:27017/
DB_MONGODB_PASSWORD=yourpassword

# API credentials (get these from the respective platforms)
API_CODEFORCES_KEY=your_codeforces_key
API_CODEFORCES_SECRET=your_codeforces_secret
API_CODECHEF_CLIENT_ID=your_codechef_client_id
API_CODECHEF_CLIENT_SECRET=your_codechef_client_secret
# ... and more!
```

### 6️⃣ Verify Installation

Let's make sure everything is working:

```bash
# Run a simple verification command
python main.py --help
```

If you see the help output listing available commands, you're good to go! 🎯

## 🔧 Troubleshooting

### "ModuleNotFoundError"

If you get this error, it means a package is missing. Try:

```bash
pip install -r requirements.txt
```

### MongoDB Connection Issues

If you can't connect to MongoDB:

1. Make sure MongoDB is running: `mongod --version`
2. Check your connection string in `.env`
3. Verify network settings if using a remote MongoDB

### Platform API Authentication Errors

If you're having trouble with platform APIs:

1. Check your API credentials in `.env`
2. Make sure you're using the correct API endpoints
3. Some platforms might have rate limits - be patient!

## 🌟 Next Steps

Now that you've successfully installed Pyramid-Tracker, you're ready to:

- [Configure your settings](./configuration.md) ⚙️
- Follow the [quick start guide](./quickstart.md) 🏃‍♀️
- Explore the [CLI commands](./cli.md) 💻

Happy tracking! 🎮 