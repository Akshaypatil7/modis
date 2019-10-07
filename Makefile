## Configuration for Makefile.
SRC := blocks/nasa_modis
MANIFEST_JSON := $(SRC)/UP42Manifest.json
UP42_DOCKERFILE := $(SRC)/Dockerfile
DOCKER_TAG := nasa-modis
## Extra images needed by the block image.
NASA_MODIS_DOCKERFILE := $(SRC)/Dockerfile

VALIDATE_ENDPOINT := https://api.up42.com/validate-schema/block
REGISTRY := registry.up42.com
CURL := curl
DOCKER := docker

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
		$(CURL) -X POST -H 'Content-Type: application/json' -d @$(MANIFEST_JSON) $(VALIDATE_ENDPOINT)

build:
ifdef UID
	cd blocks/nasa_modis; $(DOCKER) build --build-arg manifest="$$(cat UP42Manifest.json)" -f $(UP42_DOCKERFILE) -t $(REGISTRY)/$(UID)/$(DOCKER_TAG) .
else
	cd blocks/nasa_modis; docker build -t nasa-modis -f Dockerfile .
endif

e2e:
	python e2e.py

available-layers:
	python blocks/nasa_modis/src/available_layers.py

.PHONY: build login push test install e2e available-layers
