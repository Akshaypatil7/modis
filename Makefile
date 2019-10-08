## Configuration for Makefile.
SRC := blocks/nasa_modis
UP42_DOCKERFILE := Dockerfile
DOCKER_TAG := nasa-modis
DOCKER_VERSION := latest

VALIDATE_ENDPOINT := https://api.up42.com/validate-schema/block
REGISTRY := registry.up42.com

install:
	pip install -r blocks/nasa_modis/requirements.txt

test:
	python -m pytest --pylint --pylint-rcfile=../../pylintrc --mypy --mypy-ignore-missing-imports --cov=blocks/nasa_modis/src/

test[live]:
	python -m pytest --pylint --pylint-rcfile=../../pylintrc --mypy --mypy-ignore-missing-imports --cov=blocks/nasa_modis/src/ --runlive

clean:
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name ".mypy_cache" -exec rm -rf {} +
	find . -name ".pytest_cache" -exec rm -rf {} +
	find . -name ".coverage" -exec rm -f {} +

validate:
	cd blocks/nasa_modis;	curl -X POST -H 'Content-Type: application/json' -d @UP42Manifest.json $(VALIDATE_ENDPOINT)

build:
ifdef UID
	cd blocks/nasa_modis; docker build --build-arg manifest="$(cat UP42Manifest.json)" -f Dockerfile -t $(REGISTRY)/$(UID)/$(DOCKER_TAG):$(DOCKER_VERSION) .
else
	cd blocks/nasa_modis; docker build -t nasa-modis -f Dockerfile .
endif

push:
	docker push $(REGISTRY)/$(UID)/$(DOCKER_TAG):$(DOCKER_VERSION)

login:
	docker login -u $(USER) https://$(REGISTRY)

e2e:
	python e2e.py

available-layers:
	python blocks/nasa_modis/src/available_layers.py

.PHONY: build login push test install e2e available-layers push login
