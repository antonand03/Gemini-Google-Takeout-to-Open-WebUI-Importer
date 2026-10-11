import json
import re
from datetime import datetime

try:
    with open('MyActivity.json', 'r', encoding='utf-8') as f:
        takeout_data = json.load(f)
except FileNotFoundError:
    print("Error: 'MyActivity.json' not found.")
    exit()

sessions = {}

def clean_html(raw_html):
    if not raw_html:
        return ""
    clean = re.sub(r'<.*?>', '', raw_html)
    clean = clean.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    return clean.strip()

def parse_timestamp(ts_str):
    if not ts_str:
        return int(datetime.now().timestamp())
    # Try common timestamp formats
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return int(datetime.strptime(ts_str, fmt).timestamp())
        except ValueError:
            pass
    return int(datetime.now().timestamp())

# 1. Parse Google Takeout chronologically
for item in takeout_data:
    # Filter items that are not instruction prompts
    if "title" not in item or not item["title"].startswith("Gave the instruction "):
        continue
        
    prompt = item["title"].replace("Gave the instruction ", "").strip()
    timestamp_str = item.get("time", "")
    
    response_html = ""
    html_items = item.get("safeHtmlItem")
    if html_items:
        if isinstance(html_items, list) and len(html_items) > 0:
            response_html = html_items[0].get("html", "")
        elif isinstance(html_items, dict):
            response_html = html_items.get("html", "")
            
    response_text = clean_html(response_html)
    if not response_text:
        response_text = "No response recorded."

    session_id = "unknown_session"
    details = item.get("details")
    if details:
        details_obj = details[0] if isinstance(details, list) and len(details) > 0 else details
        if isinstance(details_obj, dict):
            url = details_obj.get("url", "")
            # Extract session ID from URL pattern
            match = re.search(r'/app/([a-zA-Z0-9]+)', url)
            if match:
                session_id = match.group(1)
            
    if session_id not in sessions:
        sessions[session_id] = []
        
    sessions[session_id].append({
        "prompt": prompt,
        "response": response_text,
        "timestamp": timestamp_str
    })

# Final JSON must be a top-level array
final_import_array = []

# 2. Re-index into tree structures following Open WebUI standard
for session_id, turns in sessions.items():
    turns.sort(key=lambda x: x["timestamp"])
    
    # Determine chat title based on the first prompt, truncated to 40 characters
    chat_title = turns[0]["prompt"][:40] + "..." if len(turns[0]["prompt"]) > 40 else turns[0]["prompt"]
    
    messages = {}
    last_assistant_id = None
    
    for i, turn in enumerate(turns):
        # Generate unique node IDs for user and assistant turns
        user_node_id = f"user_{session_id}_{i}"
        assistant_node_id = f"assistant_{session_id}_{i}"
        
        # Determine parent and child nodes for conversational flow
        user_parent = f"assistant_{session_id}_{i-1}" if i > 0 else None
        user_child = assistant_node_id
        
        assistant_parent = user_node_id
        assistant_child = f"user_{session_id}_{i+1}" if i < len(turns) - 1 else None
        
        ts_seconds = parse_timestamp(turn["timestamp"])
        
        # User message structure
        messages[user_node_id] = {
            "id": user_node_id,
            "parentId": user_parent,
            "childrenIds": [user_child],
            "role": "user",
            "content": turn["prompt"],
            "timestamp": ts_seconds
        }
        
        # Assistant response structure
        messages[assistant_node_id] = {
            "id": assistant_node_id,
            "parentId": assistant_parent,
            "childrenIds": [assistant_child] if assistant_child else [],
            "role": "assistant",
            "content": turn["response"],
            "model": "gemini-import",
            "done": True,
            "timestamp": ts_seconds + 1
        }
        
        last_assistant_id = assistant_node_id
        
    if last_assistant_id:
        # Calculate start and end timestamps for the chat object
        first_ts = parse_timestamp(turns[0]["timestamp"])
        last_ts = parse_timestamp(turns[-1]["timestamp"]) + 1
        
        # Construct the chat object according to Open WebUI standard format
        chat_object = {
            "chat": {
                "title": chat_title,
                "models": ["gemini-import"],
                "history": {
                    "currentId": last_assistant_id,
                    "messages": messages
                }
            },
            "meta": {},
            "pinned": False,
            "folder_id": None,
            "created_at": first_ts,
            "updated_at": last_ts
        }
        final_import_array.append(chat_object)

# Save as a clean JSON array
with open('open_webui_import.json', 'w', encoding='utf-8') as f:
    json.dump(final_import_array, f, ensure_ascii=False, indent=2)

print(f"Done! Converted {len(final_import_array)} historical threads to Open WebUI Standard format.")