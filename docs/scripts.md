# 🛠️ Scripts Module Documentation

> The toolbox of handy utilities that make our lives easier! 🧰 These scripts help automate common tasks and data management.

## 📁 Module Structure

```
scripts/
├── upload_participants.py   # CSV data upload script
└── __init__.py             # Module initialization
```

## 📤 Upload Participants Script

The star of our scripts show! This script handles importing participant data from CSV files.

### 🎭 Features

```python
def upload_participants(college_name: str, batch_name: str) -> None:
    """Upload participants from CSV to MongoDB"""
```

- 📥 **CSV Import**: Reads participant data from structured CSV files
- 🧹 **Data Cleaning**: Automatically cleans and standardizes data
- ✨ **Handle Verification**: Ensures platform handles are in the correct format
- 💾 **Bulk Upload**: Efficiently uploads data to MongoDB

### 🎮 How to Use

```bash
# Through CLI
python main.py upload-users --college CMRIT --batch _2025

# Or programmatically
from scripts.upload_participants import upload_participants
upload_participants("CMRIT", "_2025")
```

### 📋 CSV Format Requirements

Your CSV file should follow the format below:

```csv
HallTicketNo,CodeChefHandle,CodeforcesHandle,GeeksForGeeksHandle,LeetCodeHandle,HackerRankHandle
20XX1A0001,john_chef,john_cf,john_gfg,john_leet,john_hack
20XX1A0002,jane_chef,jane_cf,jane_gfg,jane_leet,jane_hack
```

**Required columns:**

- 🎫 **HallTicketNo**: A unique identifier for each participant.
- 🔗 **CodeChefHandle**: Participant’s CodeChef handle.
- 🔗 **CodeforcesHandle**: Participant’s Codeforces handle.
- 🔗 **GeeksForGeeksHandle**: Participant’s GeeksForGeeks handle.
- 🔗 **LeetCodeHandle**: Participant’s LeetCode handle.
- 🔗 **HackerRankHandle**: Participant’s HackerRank handle.

**Note**: The order of columns should strictly follow this format to ensure proper parsing and standardization. The column names will be standardized automatically during the data processing.

## 🧙‍♂️ Pro Tips

1. 📝 **CSV Preparation**:
   ```python
   df = clean_handles_col(df, handle_columns=df.columns[1:])
   df = standardize_column_names(df)
   ```

2. 🔍 **Data Verification**:
   ```python
   # Verify your data after upload
   python main.py verify-users --college CMRIT --batch _2025
   ```

3. 🧪 **Testing**:
   ```python
   # Use a small sample first
   df_test = df.head(5)
   repo.bulk_upload_from_dataframe(df_test, batch, college)
   ```

## 🎯 Common Use Cases

### 1️⃣ Initial Data Import

```bash
# First-time data upload
python main.py upload-users --college CMRIT --batch _2025
```

### 2️⃣ Data Updates

```bash
# Update existing records
python main.py upload-users --college CMRIT --batch _2025 --update
```

### 3️⃣ Data Verification

```bash
# Verify uploaded data
python main.py verify-users --college CMRIT --batch _2025
```

## 🚨 Error Handling

The script handles common errors gracefully:
- 📛 **Invalid CSV Format**: Clear error messages for format issues
- 🔄 **Duplicate Entries**: Handles duplicate hall ticket numbers
- ❌ **Missing Data**: Warns about required columns
- 🌐 **Invalid Handles**: Flags invalid platform usernames

## 🔄 Data Flow

1. 📥 Read CSV file
2. 🧹 Clean and validate data
3. 🎯 Map to MongoDB schema
4. 💾 Upload to database
5. ✅ Verify upload success

## 🎨 Customization

Need to modify the script? Here are some common customization points:

```python
# Custom column mapping
COLUMN_MAPPING = {
    "Roll Number": "hall_ticket_no",
    "Student Name": "name",
    # ... add more mappings
}

# Custom data validation
def validate_handle(handle: str, platform: str) -> bool:
    # Add your validation logic
    pass
```

## 🆘 Troubleshooting

Common issues and solutions:

1. **CSV Reading Errors** 📄
   - Check file encoding (use UTF-8)
   - Verify column names match expected format
   - Look for hidden characters

2. **MongoDB Connection Issues** 🔌
   - Verify MongoDB is running
   - Check connection string in `.env`
   - Ensure proper permissions

3. **Data Validation Failures** ⚠️
   - Check for empty cells
   - Verify handle formats
   - Look for duplicate entries

---

Remember: A well-formatted CSV is a happy CSV! 📊 