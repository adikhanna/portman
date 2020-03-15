venv:
	/usr/local/bin/python3 -m venv venv
	venv/bin/pip install -r requirements.txt

typecheck: venv
	venv/bin/mypy --config-file mypy.ini ./src/*.py

format: venv
	venv/bin/autopep8 --in-place --aggressive ./src/*.py

freeze: venv
	venv/bin/pip freeze > ./requirements.txt

run_stocks: venv typecheck
	venv/bin/python ./src/yahoo_stocks.py -config ./conf/yahoo_stocks.json

run_options: venv typecheck
	venv/bin/python ./src/yahoo_options.py -config ./conf/yahoo_options.json

ui: venv typecheck
	venv/bin/python ./src/main.py -config ./conf/main.json

.PHONY: clean
clean:
	rm -rf venv
