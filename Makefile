.PHONY=build
build: # build panhan binary
	python -m nuitka \
	--nofollow-import-to=toml \
	--prefer-source-code \
	--onefile \
	src/panhan/main.py
	mv main.bin panhan.bin
