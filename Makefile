clean:


install:
	pip install -r blocks/nasa-modis/requirements.txt

test:
    python -m pytest --pylint --pylint-rcfile=../../pylintrc --mypy --mypy-ignore-missing-imports --cov=src/
