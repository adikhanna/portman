venv:
	/usr/local/bin/python3 -m venv venv
	venv/bin/pip install -r requirements.txt

typecheck: venv
	venv/bin/mypy --config-file mypy.ini ./src/*.py

format: venv
	venv/bin/autopep8 --in-place --aggressive ./src/*.py

freeze: venv
	venv/bin/pip freeze > ./requirements.txt

run: venv typecheck
	venv/bin/python ./src/price.py

.PHONY: clean
clean:
	rm -rf venv
