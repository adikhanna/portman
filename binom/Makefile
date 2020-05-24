dep:
	brew cask install wkhtmltopdf

venv: dep
	/usr/local/bin/python3 -m venv venv
	venv/bin/pip3 install -r requirements.txt

typecheck: venv
	venv/bin/mypy --config-file mypy.ini ./src/*.py

format: venv
	venv/bin/autopep8 --in-place --aggressive ./src/*.py

freeze: venv
	venv/bin/pip3 freeze > ./requirements.txt

run: venv
	venv/bin/python3 ./src/binomial_tree.py -config ./conf/tree.json

.PHONY: clean
clean:
	rm -rf venv
