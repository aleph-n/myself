"""
Processes raw markdown journal files, enriches them using the Gemini API,
and outputs a structured CSV file for analysis.

This version is optimized to process an entire day's worth of new/modified
entries in a single, batched API call to improve efficiency and reduce cost.
It uses a refined prompt with the full Plutchik's Wheel of Emotions.
"""
import os
import re
import csv
import json
import yaml
import hashlib
from typing import List, Dict

# --- Load configuration ---
CONFIG_PATH = "./config.yml"
def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
JOURNAL_DIR = config.get("journal_dir", "./data/journal")
OUTPUT_DIR = config.get("output_dir", "./output")
OUTPUT_CSV_PATH = os.path.join(OUTPUT_DIR, "myself_prompts_enriched.csv")
PROCESSING_STATE_PATH = os.path.join(OUTPUT_DIR, "journal_processing_state.json")
DEFAULT_MODEL = config.get("default_model", "gemini")
MODELS = config.get("models", {})


# --- Model setup (extensible) ---
def setup_model(model_name):
    if model_name == "gemini" and MODELS.get("gemini", {}).get("enabled"):
        import google.generativeai as genai
        api_key = MODELS["gemini"].get("api_key")
        if not api_key:
            raise ValueError("Gemini API key not found in config.yml.")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(MODELS["gemini"].get("model_name", "gemini-2.5-pro"))
    elif model_name == "openai" and MODELS.get("openai", {}).get("enabled"):
        # Placeholder for OpenAI setup
        pass
    else:
        raise ValueError(f"Model '{model_name}' is not enabled or not supported.")

def get_entry_hash(entry_text: str) -> str:
    """Creates a unique SHA-256 hash for a given text entry."""
    return hashlib.sha256(entry_text.encode('utf-8')).hexdigest()

def load_processing_state() -> dict:
    """Loads the processing state file if it exists."""
    if os.path.exists(PROCESSING_STATE_PATH):
        with open(PROCESSING_STATE_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_processing_state(state: dict):
    """Saves the updated processing state to a file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(PROCESSING_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def enrich_batch(entries: List[Dict[str, str]], model_name: str = DEFAULT_MODEL) -> List[Dict]:
    """
    Sends a batch of text entries to the selected enrichment model.
    """
    model = setup_model(model_name)
    prompt_text = "\n".join([f"{i+1}. {entry['original_text']}" for i, entry in enumerate(entries)])
    prompt = f"""
    You are a psychological and behavioral analysis assistant.
    Analyze the following list of text entries. For each entry, return a corresponding JSON object.
    The final output must be a single, minified JSON array containing one object for each entry.

    The source text may be in English, Spanish, or a mix of both. Translate any Spanish to American English.

    For each entry, perform these three analyses:
    1.  **Sentiment Analysis:** Classify the emotional tone. Use one of: [Positive, Negative, Neutral].
    2.  **Emotion Analysis:** Identify the specific dominant emotion based on Plutchik's model. Use one of the 8 primary emotions, a key secondary emotion (dyad), or Informative/Objective.
        - Primary Emotions: [Joy, Trust, Fear, Surprise, Sadness, Disgust, Anger, Anticipation].
        - Secondary Emotions (Dyads): [Love, Submission, Awe, Disapproval, Remorse, Contempt, Aggressiveness, Optimism].
        - If no emotion is present, use "Informative/Objective".
    3.  **Behavioral Analysis:** Classify the user's intent based on Speech Act Theory. Use one of: [Instructional (Directive), Inquisitive (Question), Declarative (Assertive), Expressive (Reflective)].

    Source Text Entries:
    {prompt_text}

    Return a minified JSON array `[ {{"Sentiment Analysis": "...", "Emotion Analysis": "...", "Behavioral Analysis": "..."}}, {{...}} ]` with no other text.
    """
    try:
        response = model.generate_content(prompt)
        cleaned_json = response.text.strip().replace('`', '').replace('json', '')
        return json.loads(cleaned_json)
    except Exception as e:
        print(f"Error processing batch with {model_name}: {e}")
        return []

def parse_journal_files(processing_state: dict, model_name: str = DEFAULT_MODEL):
    """
    Reads all .md files, identifies new/modified entries, processes them in batches
    per day, and returns the full, updated list of all processed entries.
    """
    entry_regex = re.compile(r"^- (\d{2}:\d{2}):\s*(.*)")
    comment_regex = re.compile(r"<!--\s*user_id:\s*([^,]+),\s*source:\s*([^\s]+)\s*-->")

    current_hashes = set()
    entries_to_process_by_day: Dict[str, List[Dict]] = {}

    for filename in sorted(os.listdir(JOURNAL_DIR)):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(JOURNAL_DIR, filename)
        date_str = filename.replace(".md", "")

        with open(filepath, "r", encoding="utf-8") as f:
            lines = [l.rstrip() for l in f]
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                match = entry_regex.match(line)
                if match:
                    entry_hash = get_entry_hash(line)
                    current_hashes.add(entry_hash)

                    # Look ahead for a comment line
                    user_id = "aleph_n"
                    source = "manual"
                    if i + 1 < len(lines):
                        comment_match = comment_regex.search(lines[i + 1])
                        if comment_match:
                            user_id = comment_match.group(1).strip()
                            source = comment_match.group(2).strip()
                            i += 1  # Skip the comment line

                    if entry_hash not in processing_state:
                        if date_str not in entries_to_process_by_day:
                            entries_to_process_by_day[date_str] = []

                        time_str, prompt_text = match.groups()
                        entries_to_process_by_day[date_str].append({
                            "hash": entry_hash,
                            "date_str": date_str,
                            "time_str": time_str,
                            "prompt_text": prompt_text,
                            "original_text": line,
                            "user_id": user_id,
                            "source": source
                        })
                i += 1

    for date_str, entries_batch in entries_to_process_by_day.items():
        print(f"✨ Found {len(entries_batch)} new/modified entries for {date_str}. Processing as a batch...")
        enriched_results = enrich_batch(entries_batch, model_name)

        if len(enriched_results) == len(entries_batch):
            for i, enriched_data in enumerate(enriched_results):
                original_entry = entries_batch[i]
                # DWH schema alignment: fact_event + fact_enrichment
                event_record = {
                    "event_type": "journal_entry",
                    "event_time": f"{original_entry['date_str']}T{original_entry['time_str']}:00",
                    "user_id": original_entry.get("user_id", "aleph_n"),
                    "payload": {
                        "prompt": original_entry['prompt_text']
                    },
                    "source": original_entry.get("source", "manual")
                }
# ---
# COMMENT METHOD ANALYSIS:
# Pros:
# - Human-readable and markdown-compatible; doesn't break rendering.
# - Survives manual editing and is easy to inspect.
# - Allows for future extensibility (add more fields if needed).
# Cons:
# - Not a formal data structure; parsing is more error-prone than YAML frontmatter or a sidecar JSON.
# - If comments are deleted or malformed, metadata is lost.
# - Not ideal for very large-scale or multi-user collaborative editing.
                # Use actual model name from config for model_name field
                actual_model_name = MODELS.get(model_name, {}).get("model_name", model_name)
                provider = model_name.split("-")[0] if "-" in model_name else model_name
                enrichment_record = {
                    "event_id": original_entry['hash'],
                    "enrichment_type": f"{actual_model_name}_analysis",
                    "enrichment_data": {
                        "sentiment": enriched_data.get("Sentiment Analysis", "Unknown"),
                        "emotion": enriched_data.get("Emotion Analysis", "Unknown"),
                        "behaviour": enriched_data.get("Behavioral Analysis", "Unknown"),
                    },
                    "model_name": actual_model_name,
                    "source": provider
                }
                # Store both event and enrichment records for future DB insert
                processing_state[original_entry['hash']] = {
                    "event": event_record,
                    "enrichment": enrichment_record
                }
        else:
            print(f"Warning: Mismatch in batch processing for {date_str}. Expected {len(entries_batch)} results, got {len(enriched_results)}.")

    stale_hashes = set(processing_state.keys()) - current_hashes
    if stale_hashes:
        print(f"Removing {len(stale_hashes)} stale entries...")
        for h in stale_hashes:
            del processing_state[h]

    return list(processing_state.values())

def main():
    """ Main function to run the optimized journal processing pipeline. """
    print("🚀 Starting batch-optimized journal processing...")

    processing_state = load_processing_state()
    enriched_entries = parse_journal_files(processing_state, model_name=DEFAULT_MODEL)


    if not enriched_entries:
        print("No new or modified entries found. CSV is up to date.")
        # Still, we should write the (potentially pruned) data back to CSV
        if os.path.exists(PROCESSING_STATE_PATH):
            final_state_list = list(load_processing_state().values())
            if final_state_list:
                # Flatten for CSV output, skip malformed records
                with open(OUTPUT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["event_time", "event_type", "prompt", "sentiment", "emotion", "behaviour", "model_name", "source"])
                    writer.writeheader()
                    for rec in final_state_list:
                        if not isinstance(rec, dict):
                            continue
                        event = rec.get("event")
                        enrichment = rec.get("enrichment")
                        if not event or not enrichment:
                            print("Skipping malformed record (missing event/enrichment):", rec)
                            continue
                        row = {
                            "event_time": event.get("event_time", ""),
                            "event_type": event.get("event_type", ""),
                            "prompt": event.get("payload", {}).get("prompt", ""),
                            "sentiment": enrichment.get("enrichment_data", {}).get("sentiment", ""),
                            "emotion": enrichment.get("enrichment_data", {}).get("emotion", ""),
                            "behaviour": enrichment.get("enrichment_data", {}).get("behaviour", ""),
                            "model_name": enrichment.get("model_name", ""),
                            "source": event.get("source", "")
                        }
                        writer.writerow(row)
        return

    save_processing_state(processing_state)


    # Flatten for CSV output, skip malformed records
    with open(OUTPUT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["event_time", "event_type", "prompt", "sentiment", "emotion", "behaviour", "model_name", "source"])
        writer.writeheader()
        for rec in enriched_entries:
            if not isinstance(rec, dict):
                continue
            event = rec.get("event")
            enrichment = rec.get("enrichment")
            if not event or not enrichment:
                print("Skipping malformed record (missing event/enrichment):", rec)
                continue
            row = {
                "event_time": event.get("event_time", ""),
                "event_type": event.get("event_type", ""),
                "prompt": event.get("payload", {}).get("prompt", ""),
                "sentiment": enrichment.get("enrichment_data", {}).get("sentiment", ""),
                "emotion": enrichment.get("enrichment_data", {}).get("emotion", ""),
                "behaviour": enrichment.get("enrichment_data", {}).get("behaviour", ""),
                "model_name": enrichment.get("model_name", ""),
                "source": event.get("source", "")
            }
            writer.writerow(row)

    print(f"\n✅ Success! {len(enriched_entries)} total entries in the dataset.")
    print(f"Enriched CSV file updated at: {OUTPUT_CSV_PATH}")

if __name__ == "__main__":
    main()


