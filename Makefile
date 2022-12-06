# Develop mode install:
install:
	python3 -m pip install -e ./

test: install
	python3 -m pytest --color=yes -raXxs
