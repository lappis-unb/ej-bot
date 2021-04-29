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


first-run: ## Build docker services, train models and put the bot to run on shell. Sucessful if by the end you can chat with the bot via terminal
	build train run-shell 

 
build: ## Build base requirements dockerfile and coach and bot services
	build-requirements build-coach build-bot build-x

build-requirements:
	docker build . --no-cache -f docker/requirements.Dockerfile -t botrequirements

build-bot:
	docker-compose build --no-cache bot

build-x:
	docker-compose build --no-cache x

build-coach:
	docker-compose build --no-cache coach

train: ## Generate a tar.gz file in bot/models/, that is used for the bot interpretation
	mkdir -p bot/models
	docker-compose up --build coach

run-duck: ## Run duckling server that extract entities such as email, number and urls
	docker-compose up -d duckling

############################## ENVIRONMENTS ##############################

run-shell: run-duck ## Run bot in shell, sucessful when shows "Bot loaded. Type a message and press enter (use '/stop' to exit): "    
	docker-compose run --name bot bot make shell

run-api: run-duck ## Run api locally, it is hosted in localhost:5006 and is used for webchat, telegram and rocketchat integrations
	docker-compose run --name bot --rm --service-ports bot make api

run-x: run-duck ## Run bot in rasa x mode locally, hosted in localhost:5002 
	docker-compose run --name rasax --rm --service-ports x make x

run-webchat: ## Run bot in web mode, hosted in localhost:8001
	docker-compose up webchat

run-actions: ## Run actions server, as an api avaiable in localhost:5055
	docker-compose run -d --name actions --rm --service-ports actions make actions


############################## TESTS ##############################
test: run-duck ## Run tests in bot/tests/test_stories.yml
	docker-compose run --name bot --rm bot make test

test-actions: ## Run tests in bot/tests/ that  are in files of type .py (python files)
	docker-compose run --rm bot make test-actions

run-test-nlu:
	docker-compose run --name bot --rm bot make test-nlu

run-test-core:
	docker-compose run  --name bot --rm bot make test-core


validate:
	docker-compose run  --name bot --rm bot rasa data validate --domain domain.yml --data data/ -vv

visualize:
	docker-compose run --name coach --rm  -v $(current_dir)/bot:/coach coach rasa visualize --domain domain.yml --stories data/stories.md --config config.yml --nlu data/nlu.md --out ./graph.html -vv
	$(info )
	$(info Caso o FIREFOX não seja iniciado automáticamente, abra o seguinte arquivo com seu navegador:)
	$(info bot/graph.html)
	firefox bot/graph.html
