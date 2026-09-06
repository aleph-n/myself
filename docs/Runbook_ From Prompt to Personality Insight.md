# **Runbook: From Prompt to Personality Insight**

This document outlines the data pipeline for the "myself" project. The goal is to transform raw, unstructured log entries (the "raw artifact") into structured, enriched data rows with personality insights (the "extended classification artifact") inside the PostgreSQL data warehouse.

The pipeline consists of three main stages: Capture, Enrich, and Load.

### **Stage 1: Data Capture (The Raw Artifact)**

This stage is about getting your thoughts and actions from your head into a file with minimal friction.

* **Trigger:** You, the user, execute the make log TEXT="..." command from the terminal.  
* **Process:**  
  1. The Makefile command invokes the src/journal.py script inside the api Docker container.  
  2. src/journal.py takes your verbatim text, prepends the current America/Mexico\_City timestamp, and appends it to the correct daily log file (e.g., data/journal/2025-10-15.md).  
* **Output (Raw Artifact):** A single line in a markdown file. This artifact is unstructured, written in natural language (Spanglish), and contains the rawest form of your data.Example: \- 14:30: Leí un capítulo de "Superintelligence".

### **Stage 2: Enrichment (The AI Transformation)**

This is the core transformation stage where raw data is converted into structured insight. This will be handled by a new, central ingestion script (src/ingest.py).

* **Trigger:** You run a new command, like make ingest, which executes src/ingest.py.  
* **Process:**  
  1. **Extract:** The script scans the data/journal/ directory, reading all markdown files that haven't been processed yet.  
  2. **Pre-process:** It parses each line, separating the timestamp from the raw text.  
  3. **Enrich via AI:** For each prompt, the script makes a call to an AI model (e.g., Gemini API) with a detailed set of instructions to perform multiple tasks in one pass:  
     * **Translate & Standardize:** Convert Spanglish into consistent English.  
     * **Categorize:** Assign a primary category (e.g., "Python Scripting", "Personal Reflection").  
     * **Analyze Sentiment:** Determine if the tone is Positive, Negative, or Neutral.  
     * **Identify Emotion:** Classify the dominant emotion (e.g., Anticipation, Sadness).  
     * **Analyze Behavior:** Determine the intent (e.g., Instructional, Inquisitive).  
* **Output (Intermediate Artifact):** The AI returns a structured JSON object for each prompt.Example JSON:  
  {  
    "timestamp": "2025-10-15T14:30:00-06:00",  
    "prompt\_clean": "I read a chapter of 'Superintelligence'.",  
    "category": "Knowledge & Research",  
    "sentiment": "Neutral",  
    "emotion": "Neutral/Informative",  
    "behaviour": "Declarative"  
  }

### **Stage 3: Load (Storing the Enriched Artifact)**

The final stage is loading the structured, enriched data into your PostgreSQL data warehouse.

* **Trigger:** This happens within the same src/ingest.py script immediately after the enrichment stage.  
* **Process:**  
  1. The script establishes a connection to the PostgreSQL database running in the db container.  
  2. It iterates through the JSON objects received from the AI.  
  3. For each object, it constructs and executes an INSERT statement to load the data into a new, dedicated table (e.g., fact\_prompts or fact\_journal\_entries).  
* **Output (Final Artifact):** A new row in your DWH. This is the "extended classification" artifact, ready for complex queries and visualization.

### **Integration into the myself Project**

This entire pipeline is designed to live within your existing Docker environment. The src/ingest.py script will be part of the api service and will have access to both the data/ directory (to read logs) and the db service (to write results). The process will be managed and automated via simple Makefile commands.