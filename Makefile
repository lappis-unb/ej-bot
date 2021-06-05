current_dir := $(shell pwd)
user := $(shell whoami)

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: ## Bring down the bot and cleans database and trained models
	docker-compose down
	cd bot/ && make clean

stop: ## Runs docker-compose stop commmand
	docker-compose stop

############################## BOILERPLATE ##############################

build-requirements:
	docker build . -f docker/requirements.Dockerfile -t botrequirements

build: build-requirements build-coach build-bot build-x

build-bot:
	docker-compose build bot

build-x:
	docker-compose build x

build-coach:
	docker-compose build coach

## Generate a tar.gz file in bot/models/, that is used for the bot interpretation
train:
	mkdir -p bot/models
	docker-compose up coach

## Run duckling server that extract entities such as email, number and urls
run-duck:
	docker-compose up -d duckling

## Prepare bot image and train the first model
prepare: build train

############################## ENVIRONMENTS ##############################

run-shell: run-duck ## Run bot in shell, sucessful when shows "Bot loaded. Type a message and press enter (use '/stop' to exit): "    
	docker-compose run --name bot bot make shell

## Run api locally, it is hosted in localhost:5006 and is used for webchat, telegram and rocketchat integrations
run-api: run-duck
	docker-compose up bot

run-x: run-duck ## Run bot in rasa x mode locally, hosted in localhost:5002 
	docker-compose run --name rasax --rm --service-ports x make x

run-webchat: ## Run bot in web mode, hosted in localhost:8001
	docker-compose up webchat

## Run actions server, as an api avaiable in localhost:5055
run-actions: 
	docker-compose up actions

run-cron: ## Install and run cron for deleting models automatically
	docker-compose run --name bot bot docker/run-cron.sh

############################## TESTS ##############################
test: run-duck ## Run tests in bot/tests/test_stories.yml
	docker-compose up -d bot
	docker-compose exec bot make test

test-actions: ## Run tests in bot/tests/ that  are in files of type .py (python files)
	docker-compose up -d bot
	docker-compose exec bot make test-actions

test-nlu:
	docker-compose up -d bot
	docker-compose exec bot make test-nlu

test-core:
	docker-compose up -d bot
	docker-compose exec bot make test-core


validate:
	docker-compose run  --name bot --rm bot rasa data validate --domain domain.yml --data data/ -vv

visualize:
	docker-compose run --name coach --rm  -v $(current_dir)/bot:/coach coach rasa visualize --domain domain.yml --stories data/stories.md --config config.yml --nlu data/nlu.md --out ./graph.html -vv
	$(info )
	$(info Caso o FIREFOX não seja iniciado automáticamente, abra o seguinte arquivo com seu navegador:)
	$(info bot/graph.html)
	firefox bot/graph.html
