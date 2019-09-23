install:
	pip install -r blocks/nasa_modis/requirements.txt

test:
	python -m pytest --pylint --pylint-rcfile=../../pylintrc --mypy --mypy-ignore-missing-imports --cov=src/

test[live]:
	python -m pytest --pylint --pylint-rcfile=../../pylintrc --mypy --mypy-ignore-missing-imports --cov=src/ --runlive

clean:
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name ".mypy_cache" -exec rm -rf {} +
	find . -name ".pytest_cache" -exec rm -rf {} +
	find . -name ".coverage" -exec rm -f {} +

.PHONY validate:
	curl -X POST -H 'Content-Type: application/json' -d @./blocks/nasa_modis/UP42Manifest.json https://api.up42.com/validate-schema/block

build-image:
	cd blocks/nasa_modis; docker build -t nasa-modis -f Dockerfile .

e2e:
	python e2e.py
