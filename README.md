

# Gemini Google Takeout to Open WebUI Importer

This script converts the raw, messy data exported by Google Takeout into a clean, structured JSON format that is compatible with Open WebUI.

If you have pulled your chat history from Google Takeout, you know the resulting JSON is difficult to use. It is full of junk, poorly structured, and not ready for import. This script handles that cleanup and reorganization for you.

**In short**: It takes your raw Google Activity JSON and transforms it into a standard, importable chat log.

## Prerequisites

Before running the script, ensure you have the following:

- **Python**: Python 3.x installed.
- **Input File**: The Google Takeout export, specifically MyActivity.json, must be placed in the same folder as the Python script.

## How to Use

Getting this done is quick and simple.
1. Setup
Ensure MyActivity.json is in the same directory as the Python file.

2. Execution
Run the script from your terminal:
```bash
python main.py
```

3. Review the Output
If successful, the script will print a confirmation message, specifying how many historical threads were processed. A new file, *open_webui_import.json*, will be created in that same directory. This is the file you use for the import process in Open WebUI.

## Technical Overview
For context, here is what the script is doing:
- **Data Loading & Filtering**: The script loads MyActivity.json and filters entries, specifically looking for prompts that start with "Gave the instruction" to identify valid conversation starts.
- **Data Cleaning**: It uses regular expressions to strip out all HTML tags and replaces common character entities (&quot;, &amp;, etc.) to ensure clean text.
- **Session Grouping**: It identifies a unique session_id from the activity URL details. This ID is critical, as it allows the script to group all related messages belonging to a single conversation.
- **Conversational Tree Building**: Instead of just creating a list, the script constructs a dependency tree structure. Each user message and assistant response is treated as a node, and they are linked using parentId and childrenIds to accurately represent the back-and-forth flow required by the Open WebUI format.
- **Final Output**: All completed conversation trees are compiled into a single top-level array in open_webui_import.json.
## Notes
- **Timestamps**: The script includes logic to handle various timestamp formats found in Takeout data, but complex or unusual date strings may require manual review.
- **Naming Convention**: The chat title is generated from the first prompt and is capped at 40 characters, matching the expected format.
- **Error Handling**: The script checks for the existence of MyActivity.json and exits gracefully if the file is missing.