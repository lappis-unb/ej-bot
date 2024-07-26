.PHONY: train

clean: ## Bring down the bot and cleans database and trained models
	docker compose down
	cd bot/ && make clean

stop: ## Runs docker-compose stop commmand
	docker compose stop

############################## BOILERPLATE ##############################

attach:
	docker exec -it bot bash

build:
	sudo rm -rf bot/.rasa && docker compose build --no-cache

## Generate a tar.gz file in bot/models/, that is used for the bot interpretation
train:
	mkdir -p bot/models
	docker compose up coach

## Prepare bot image and train the first model
prepare: build train

############################## ENVIRONMENTS ##############################

run-duck:
	docker compose up -d duckling

# Run api locally, it is hosted in localhost:5006 and is used for webchat, telegram and rocketchat integrations

run-store:
	docker compose up redis postgres

run-api: run-duck
	docker compose up bot

# Run actions server, as an api avaiable in localhost:5055
run-actions: 
	docker compose up actions

test: run-duck ## Run tests in bot/tests/test_stories.yml
	docker compose up -d bot
	docker compose exec bot make test

test-actions: ## Run tests in bot/tests/ that  are in files of type .py (python files)
	docker compose up -d bot
	docker compose exec bot make test-actions

validate:
	docker compose up -d bot
	docker compose exec bot make validate

