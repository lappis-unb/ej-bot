.PHONY: all clean actions

clean:
	rm -rf graph.html results/ models/* *.db*

install:
	pip install --upgrade pip && \
	pip install -r ../requirements.txt && \
	pip install -r ../x-requirements.txt

# CORE
train:
	rasa train -vv --domain domain.yml

# TESTS
test:
	rasa test --out results/ --fail-on-prediction-errors --nlu data/nlu.yml --cross-validation

test-actions:
	python -m pytest

# VALIDACAO
validate:
	rasa data validate -vv --data data/ -vv

# MENSAGEIROS
shell:
	rasa shell -m models/ -vv --endpoints endpoints.yml --port 5005

api:
	rasa run -m models/ -vv --credentials credentials.${ENV}.yml --endpoints endpoints.yml --enable-api --port 5006 --auth-token thisismysecret --cors "*"

# ACTIONS
actions:
	rasa run actions -vv --debug --auto-reload
