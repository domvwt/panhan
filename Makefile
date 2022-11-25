.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

.PHONY=help
help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

.PHONY=clean
clean: ## clean build artifacts
	rm -rf build
	rm -rf *.build
	rm -rf *.dist
	rm -rf *.bin
	rm -rf **/*.egg-info

build: clean ## build panhan binary
	python -m nuitka \
	--nofollow-import-to=toml \
	--prefer-source-code \
	--onefile \
	src/panhan/__main__.py
	mv __main__.bin panhan.bin
	chmod a+x panhan.bin

.PHONY=install
install: ## install panhan in /usr/local/bin
	sudo ln -sf $$(readlink -e panhan.bin) /usr/local/bin/panhan

.PHONY=cqa
cqa: ## code quality analysis
	black src
	isort src
	flake8 src
	mypy src
	pylint src