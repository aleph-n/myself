# Makefile for the "myself" project

.PHONY: build up down logs clean backup log

# Builds and starts the containers in detached mode
build:
	@echo "Building and starting containers..."
	docker-compose up --build -d

# ... (other commands like up, down, logs remain the same) ...

# Backs up a dimension table to a CSV file in data/backups/
backup:
	@echo "Backing up dim_location table to CSV..."
	docker-compose exec -T db psql -U myself_user -d myself_dwh -c "\copy (SELECT * FROM dim_location) TO '/backup/dim_location_$(shell date +%Y%m%d_%H%M%S).csv' WITH (FORMAT CSV, HEADER);"

# New command to add a journal entry via the utility script
log:
	@if [ -z "$(TEXT)" ]; then \
		echo "Usage: make log TEXT=\"Your natural language entry\""; \
		exit 1; \
	fi
	@echo "Adding entry to journal..."
	docker-compose run --rm api python src/journal.py "$(TEXT)" # <-- Updated script name

# Stops containers, removes volumes, and clears output/backup folders
clean:
	@echo "Stopping containers and removing all volumes..."
	docker-compose down -v
	@echo "Cleaning output and backup directories..."
	rm -rf ./output/logs/* ./data/backups/*

# New command to import historical data from conversations.json
import-history:
	@echo "Running conversation history import..."
	docker-compose run --rm api python src/import_history.py data/history/conversations_gpt.json
    
# Processes raw journal files and creates the enriched CSV
process-journal:
	@echo "Processing journal files to create enriched CSV..."
	docker-compose run --rm api python src/process_journal.py