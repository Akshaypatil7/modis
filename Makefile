install:
	pip install -r blocks/nasa-modis/requirements.txt

test:
	python -m pytest --pylint --pylint-rcfile=../../pylintrc --mypy --mypy-ignore-missing-imports --cov=src/

clean:
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name ".mypy_cache" -exec rm -rf {} +
	find . -name ".pytest_cache" -exec rm -rf {} +
	find . -name ".coverage" -exec rm -f {} +

.PHONY validate:
	curl -X POST -H 'Content-Type: application/json' -d @./blocks/nasa_modis/UP42Manifest.json https://api.up42.com/validate-schema/block

.ONESHELL:
build-image:
	cd blocks/nasa_modis
	docker build -t nasar-modis -f Dockerfile .

e2e:
	python e2e.py
