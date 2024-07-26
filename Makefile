.PHONY: train

# Bring down the bot and cleans database and trained models
clean: 
	docker compose down
	cd bot/ && make clean

# Runs docker-compose stop commmand
stop: 
	docker compose stop


attach:
	docker exec -it bot bash

build:
	sudo rm -rf bot/.rasa && docker compose build --no-cache

# Generate a tar.gz file in bot/models/, that is used for the bot interpretation
train:
	mkdir -p bot/models
	docker compose up coach

# Prepare bot image and train the first model
prepare: build train

run-duck:
	docker compose up -d duckling

run-store:
	docker compose up redis postgres

run-api: run-duck
	docker compose up bot

# Run actions server, as an api avaiable in localhost:5055
run-actions:
	docker compose up actions
	
# Run tests in bot/tests/test_stories.yml
test: run-duck
	docker compose up -d bot
	docker compose exec bot make test
	
# Run tests in bot/tests/ that  are in files of type .py (python files)
test-actions:
	docker compose up -d bot
	docker compose exec bot make test-actions

validate:
	docker compose up -d bot
	docker compose exec bot make validate

