install:
	/usr/bin/python3 -m venv venv
	venv/bin/pip install -r requirements.txt

typecheck:
	venv/bin/mypy --config-file mypy.ini *.py

format:
	venv/bin/autopep8 --in-place --aggressive *.py

freeze:
	venv/bin/pip freeze > ./requirements.txt

run:
	venv/bin/python ./app.py -config ./matrix.json

build:
	docker build . -t app

docker:
	docker run -t app -p 5000:5000 

.PHONY: clean
clean:
	rm -rf venv
