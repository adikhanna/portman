install:
	/usr/bin/python3 -m venv venv
	venv/bin/pip install -r requirements.txt

typecheck: venv
	venv/bin/mypy --config-file mypy.ini *.py

format: venv
	venv/bin/autopep8 --in-place --aggressive *.py

freeze: venv
	venv/bin/pip freeze > ./requirements.txt

run: venv
	venv/bin/python ./app.py -config ./matrix.json

.PHONY: clean
clean:
	rm -rf venv
