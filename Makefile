.PHONY=build
build: # build panhan binary
	python -m nuitka \
	--nofollow-import-to=toml \
	--prefer-source-code \
	--onefile \
	-o dist/panhan \
	src/panhan/main.py
