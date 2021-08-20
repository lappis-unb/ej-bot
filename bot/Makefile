.PHONY: all clean actions

clean:
	rm -rf graph.html results/ models/* *.db*

install:
	pip install --upgrade pip && \
	pip install -r ../requirements.txt && \
	pip install -r ../x-requirements.txt

# RASA X
rasa-x:
#pip3 install rasa-x --extra-index-url https://pypi.rasa.com/simple
	rasa x --domain $(domain) --no-prompt --enable-api

# NLU
train-nlu:
	rasa train nlu -vv

# CORE
train:
	rasa train -vv --domain $(domain)

# TESTS
test:
	rasa test --out results/ --fail-on-prediction-errors

test-actions:
	python -m pytest

test-nlu:
	rasa test nlu --nlu data/nlu.yml --cross-validation

test-core:
	rasa test core --fail-on-prediction-errors --out results/results-core-test

# VALIDACAO
validate:
	rasa data validate -vv

# MENSAGEIROS
shell:
	rasa shell -m models/ -vv --endpoints endpoints.yml --port 5006

api:
	rasa run -m models/ -vv --credentials credentials.${ENV}.yml --endpoints endpoints.yml --enable-api --port 5006 --auth-token thisismysecret --cors "*"

# ACTIONS
actions:
	rasa run actions --actions actions -vv --debug --auto-reload
