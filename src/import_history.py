"""
This script processes a ChatGPT conversations.json export file.

It extracts all user-written prompts, converts their timestamps to the
'America/Mexico_City' timezone, and organizes them into daily markdown
journal files in the 'data/journal/' directory.

This serves as the primary tool for importing historical data into the
'myself' project.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

# --- Configuration ---
TIMEZONE = ZoneInfo("America/Mexico_City")
OUTPUT_DIR = "data/journal"

def transform_conversations(json_file_path: str):
    """
    Reads a conversations.json file, processes all user prompts, and
    writes them to daily markdown files.

    Args:
        json_file_path (str): The path to the conversations.json file.
    """
    print(f"Starting import from '{json_file_path}'...")

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{json_file_path}' was not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{json_file_path}'.", file=sys.stderr)
        sys.exit(1)

    # Use defaultdict to easily group prompts by date
    prompts_by_date = defaultdict(list)
    total_prompts_processed = 0

    # 1. Extract and Group All User Prompts
    for conversation in conversations:
        mapping = conversation.get("mapping", {})
        for node_id, node_data in mapping.items():
            message = node_data.get("message")
            if (
                message
                and message.get("author", {}).get("role") == "user"
                and message.get("create_time")
            ):
                content = message.get("content", {}).get("parts", [""])[0]
                if content and isinstance(content, str) and content.strip():
                    # Convert UTC timestamp to the target timezone
                    utc_dt = datetime.fromtimestamp(message["create_time"])
                    local_dt = utc_dt.astimezone(TIMEZONE)

                    date_str = local_dt.strftime("%Y-%m-%d")
                    time_str = local_dt.strftime("%H:%M")

                    # Store the formatted time, raw prompt, and metadata
                    prompts_by_date[date_str].append({
                        "time_str": time_str,
                        "prompt_text": content.strip(),
                        "user_id": "aleph_n",
                        "source": "gpt"
                    })
                    total_prompts_processed += 1

    print(f"Found {total_prompts_processed} total user prompts across {len(prompts_by_date)} days.")

    # 2. Write the Grouped Prompts to Markdown Files
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files_created = 0
    for date_str, prompts in sorted(prompts_by_date.items()):
        file_path = os.path.join(OUTPUT_DIR, f"{date_str}.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# My Life Log: {date_str}\n\n")
            f.write("## Prompts & Interactions\n")
            # Sort prompts by time for chronological order
            for entry in sorted(prompts, key=lambda x: x["time_str"]):
                # Write prompt with metadata as a comment for downstream processing
                f.write(f"- {entry['time_str']}: {entry['prompt_text']}\n")
                f.write(f"  <!-- user_id: {entry['user_id']}, source: {entry['source']} -->\n")
        files_created += 1

    print(f"✅ Successfully created {files_created} journal files in '{OUTPUT_DIR}'.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/import_history.py <path_to_conversations.json>", file=sys.stderr)
        sys.exit(1)
    
    json_path = sys.argv[1]
    transform_conversations(json_path)
