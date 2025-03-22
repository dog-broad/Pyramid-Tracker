# 🧰 Utils Module Documentation

> The Swiss Army knife of our codebase! 🔧 These utility functions make everyone's life easier.

## 📁 Module Structure

```
utils/
├── df_utils.py           # DataFrame manipulation utilities
├── leetcode_utils.py     # LeetCode API helpers
├── hackerrank_utils.py   # HackerRank data processing
├── gfg_utils.py          # GeeksForGeeks helpers
├── codeforces_utils.py   # Codeforces data utilities
└── __init__.py          # Module initialization
```

## 📊 DataFrame Utilities (`df_utils.py`)

Your best friend for data wrangling! 🤹‍♂️

```python
from utils.df_utils import clean_handles_col, standardize_column_names

# Clean those messy handles
df = clean_handles_col(df, handle_columns=['CodeChef', 'Codeforces'])

# Make column names consistent
df = standardize_column_names(df)
```

### 🧹 Key Functions

- 🧼 **clean_handles_col**: Sanitize platform usernames by removing unwanted characters
- 🧹 **clean_handle**: Clean individual handles (removes emails, non-ASCII chars, etc.)
- 📝 **standardize_column_names**: Normalize column names to our standard format
- ✨ **remove_non_ascii**: Strip out those pesky non-ASCII characters
- 📧 **is_email**: Check if a string looks like an email address

## 🎯 Platform-Specific Utilities

### 🏆 LeetCode (`leetcode_utils.py`)

```python
from utils.leetcode_utils import extract_leetcode_rating, format_graphql_query

# Get a user's rating
rating, raw_data = extract_leetcode_rating(api_response)

# Format a GraphQL query for the API
query = format_graphql_query("awesome_coder")

# Extract detailed user info
user_info = extract_user_info(api_response)
```

### 👨‍💻 HackerRank (`hackerrank_utils.py`)

```python
from utils.hackerrank_utils import get_contest_urls_for_college_batch

# Get contest URLs for a specific college and batch
contest_urls = get_contest_urls_for_college_batch(College.CMRIT, Batch._2025)

# Extract contest ID from URL
contest_id = extract_contest_id(contest_url)

# Load contest configuration
config = load_contests_config()
```

### 🎓 GeeksForGeeks (`gfg_utils.py`)

```python
from utils.gfg_utils import calculate_gfg_rating, extract_practice_score

# Calculate overall GFG rating
rating = calculate_gfg_rating(weekly_rating=1500, practice_rating=1200)

# Extract practice scores
practice_score, raw_data = extract_practice_score(api_response)

# Get weekly contest scores
weekly_score, contest_data = extract_weekly_contest_score(leaderboard_entries)
```

### 🏋️‍♂️ Codeforces (`codeforces_utils.py`)

```python
from utils.codeforces_utils import generate_api_sig, generate_random_string

# Generate random string for API requests
random_str = generate_random_string(6)

# Create API signature
api_sig = generate_api_sig(random_str, "user.info", "awesome_coder", timestamp, secret, api_key)
```

## 🎮 Common Use Cases

### 1️⃣ Data Cleaning

```python
# Clean up participant handles
def clean_participant_data(df):
    platform_columns = ['CodeChef', 'Codeforces', 'GeeksForGeeks', 'LeetCode', 'HackerRank']
    df = clean_handles_col(df, handle_columns=platform_columns)
    df = standardize_column_names(df)
    return df
```

### 2️⃣ Platform API Integration

```python
# Prepare Codeforces API request
random_str = generate_random_string(6)
api_sig = generate_api_sig(random_str, "user.info", handle, timestamp, secret, api_key)

# Get LeetCode user data
query = format_graphql_query(username)
rating, data = extract_leetcode_rating(response)
```

### 3️⃣ Contest Management

```python
# Get contest information
contests = get_contest_urls_for_college_batch(college, batch)
for url in contests:
    contest_id = extract_contest_id(url)
    # Process contest data
```

## 🧪 Pro Tips

1. 🎯 **Handle Cleaning**
   ```python
   # Always clean handles before processing
   clean_handle = df_utils.clean_handle(raw_handle)
   ```

2. 📊 **Rating Calculations**
   ```python
   # For GFG, combine weekly and practice scores
   rating = calculate_gfg_rating(weekly_rating, practice_rating)
   ```

3. 🔄 **API Authentication**
   ```python
   # Generate secure API signatures for Codeforces
   sig = generate_api_sig(random_str, method, handle, time, secret, key)
   ```

## 🚨 Error Handling

Our utilities handle common errors gracefully:

```python
# Handle missing API responses
try:
    rating, data = extract_leetcode_rating(response)
except:
    rating, data = 0.0, {}

# Handle invalid handles
clean_handle = clean_handle(raw_handle) or None
```

## 🎨 Customization

Need to add your own utility? Here's a template:

```python
def my_awesome_utility(data: Dict[str, Any]) -> Any:
    """
    Your awesome utility function! 🌟
    
    Args:
        data: The data to process
        
    Returns:
        Processed data
    """
    # Your magic here ✨
    return processed_data
```

## 🔍 Debugging Tips

1. 🔍 **Check Handle Formats**
   ```python
   # Print cleaned handle for verification
   print(f"Original: {handle} -> Cleaned: {clean_handle(handle)}")
   ```

2. 📊 **Verify API Responses**
   ```python
   # Extract and check user info
   user_info = extract_user_info(response)
   print(f"User rating: {user_info.get('rating', 0)}")
   ```

## 🏃‍♂️ Performance Tips

1. 🚀 **Handle Cleaning**
   ```python
   # Use vectorized operations for DataFrames
   df['clean_handles'] = df['handles'].apply(clean_handle)
   ```

2. 💾 **Contest Config**
   ```python
   # Load contest config once and reuse
   contests_config = load_contests_config()
   urls = get_contest_urls_for_college_batch(college, batch, contests_config)
   ```

---

## 📝 When to Create a New Utility

1. **General Utilities**: If the function is not specific to a particular platform, create a new utility in the `utils` folder.
2. **Platform-Specific Utilities**: If the function is specific to a platform, create a new utility with the name `{platform}_utils.py` in the `utils` folder.

---

## ❓ Do I Need a New Utility?

Consider creating a new utility if the function:

1. Handles data from a new platform.
2. Interacts with a new API.
3. Processes data from a new website.
4. Handles a new file type.
5. Interacts with a new database.
6. Works with a new cache mechanism.

If the answer is **yes** to any of these questions, it's time to create a new utility.

---

## 📝 How to Add a New Utility

1. **Create the Utility File**: Create a new file in the `utils` folder (or `platforms` folder if platform-specific).
2. **Add the Function**: Implement the utility function in the newly created file.
3. **Update Documentation**: Add the utility function to the README.md or any relevant documentation to ensure others can understand and use it.

---

Remember: These utils are your friends in the coding journey! 🤝 

Happy coding! 🚀✨