"""
Utility for the 'make log' command. Appends entries to the daily journal file.

This script is the entry point for the "Capture" stage of the data pipeline.
It handles multi-line inputs intelligently, distinguishing between a single
continuous thought and a list of pre-formatted entries.
"""
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# --- Configuration ---
TIMEZONE = ZoneInfo("America/Mexico_City")
JOURNAL_PATH = "./data/journal"

def process_and_write_entry(log_filepath: str, text_input: str):
    """
    Processes a text input and appends it to the log file.

    - If the first line is already timestamped, it processes line-by-line.
    - Otherwise, it treats the entire block as a single entry with one timestamp.
    """
    # Regex to check if a line is already timestamped.
    timestamp_regex = re.compile(r"^\s*-\s*\d{2}:\d{2}")
    current_time_str = datetime.now(tz=TIMEZONE).strftime("%H:%M")
    
    cleaned_input = text_input.strip()
    lines = cleaned_input.split('\n')
    output_content = ""

    if timestamp_regex.match(cleaned_input):
        # --- SCENARIO 1: Input is a list of pre-formatted entries ---
        # Process each line individually as before.
        output_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Ensure consistent formatting
            if line.startswith("-"):
                output_lines.append(line)
            else:
                output_lines.append(f"- {line}")
            # Always append metadata comment after each entry
            output_lines.append(f"  <!-- user_id: aleph_n, source: manual -->")
        output_content = "\n".join(output_lines) + "\n"
    else:
        # --- SCENARIO 2: Input is a single, continuous thought (possibly multi-line) ---
        # Prepend a single timestamp to the entire block.
        # Indent subsequent lines for better readability in markdown.
        first_line = f"- {current_time_str}: {lines[0]}"
        indented_lines = [f"  {line.strip()}" for line in lines[1:]]
        # Always append metadata comment after the entry
        output_content = "\n".join([first_line] + indented_lines + ["  <!-- user_id: aleph_n, source: manual -->"]) + "\n"

    # Append the processed content to the journal file.
    with open(log_filepath, "a", encoding="utf-8") as f:
        today_str = datetime.now(tz=TIMEZONE).strftime('%Y-%m-%d')
        if f.tell() == 0:
            f.write(f"# Journal: {today_str}\n\n")
        
        f.write(output_content)

def main():
    """
    Main function to process a text input and append it to today's journal file.
    """
    try:
        input_text = sys.argv[1]
    except IndexError:
        print("Error: No text provided to log.", file=sys.stderr)
        sys.exit(1)

    today = datetime.now(tz=TIMEZONE)
    log_filename = os.path.join(JOURNAL_PATH, f"{today.strftime('%Y-%m-%d')}.md")

    os.makedirs(JOURNAL_PATH, exist_ok=True)
    
    process_and_write_entry(log_filename, input_text)

    print(f"Successfully added entry to {log_filename}")

if __name__ == "__main__":
    main()

