#!/bin/bash
echo "#!/bin/sh
pipenv run isort --profile black .
pipenv run black .
git add -A
pipenv run python _lint.py
" > .git/hooks/pre-commit;
echo "[MASTER]
jobs=4
[MESSAGES CONTROL]
disable=missing-function-docstring,missing-class-docstring,missing-module-docstring,broad-exception-caught,too-few-public-methods,unknown-option-value,broad-exception-raised
[BASIC]
good-names=Authorize" > .pylintrc;
echo "[tool.black]
line-length = 90
target-version = ['py310','py311']
include = '\.pyi?$'
exclude = '''
/(
  \.toml
  |\.sh
  |\.git
  |\.ini
  |Dockerfile
)/
'''
[tool.isort]
profile = \"black\"" > pyproject.toml;
chmod +x .git/hooks/pre-commit;