PY := .venv/bin/python

.PHONY: help setup build check serve bundle next next-dev clean

help:
	@echo "make setup      create .venv and install the build dependencies"
	@echo "make check      parse and validate content, write nothing"
	@echo "make build      build the static site into dist/"
	@echo "make serve      build, then serve dist/ on :8000"
	@echo "make bundle     build + regenerate the Next.js content bundle"
	@echo "make next       bundle, then static-export the Next.js app into next/out/"
	@echo "make next-dev   bundle, then run the Next.js dev server"

setup:
	python3 -m venv .venv
	$(PY) -m pip install -q -r tools/requirements.txt
	cd next && npm install

check:
	$(PY) tools/build.py --check

build:
	$(PY) tools/build.py

serve:
	$(PY) tools/build.py --serve

bundle:
	$(PY) tools/build.py --bundle

next: bundle
	cd next && npx next build

next-dev: bundle
	cd next && npx next dev

clean:
	rm -rf dist next/out next/.next
