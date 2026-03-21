.PHONY: install run lint typecheck check docs doccheck docsclean clean

install:
	pip install -r requirements.txt -r requirements-dev.txt

run:
	python app.py

lint:
	python lint.py .

typecheck:
	mypy app.py models/ controllers/

check: lint typecheck

docs:
	sphinx-build -b html docs_sphinx docs_html

doccheck:
	pydocstyle models/ controllers/ database.py

docsclean:
	rm -rf docs_html

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
