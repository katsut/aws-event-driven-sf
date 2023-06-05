#!/bin/bash

poetry build -f wheel
poetry export -f requirements.txt --output dist/requirements.txt --without-hashes

poetry run pip install -r dist/requirements.txt --upgrade --only-binary :all: --platform linux-x86_64 --target dist/package dist/*.whl

cd dist/package

zip -r -q ../module.zip . -x '*.pyc'
