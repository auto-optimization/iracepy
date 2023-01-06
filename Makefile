# Develop mode install:
install:
	python3 -m pip install -e ./

test: install
	python3 -m pytest --color=yes -raXxs

examples: install
	@for file in examples/*.py; do \
		python3 $$file; \
	done

