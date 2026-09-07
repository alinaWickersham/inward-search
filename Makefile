.PHONY: install plan listings check-corpus test lint

install:
	pip install -e ".[corpus,dev]"

plan:            ## rebuild corpus/plan.json (deterministic, free)
	python scripts/coverage.py > corpus/plan.json

listings-try:    ## generate 5 listings to check the register
	python scripts/generate.py --limit 5

listings:        ## generate the full corpus (costs money)
	python scripts/generate.py

check-corpus:    ## validate every listing on disk against the schema
	python scripts/check_corpus.py

test:
	python -m pytest -q

lint:
	ruff check src scripts tests
