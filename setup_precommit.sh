#!/bin/bash
echo "#!/bin/sh
uv run ruff format .
uv run ruff check . --fix --exit-non-zero-on-fix
uv run pylint . -j 0 -E --fail-on E
FILES=\$(git diff --diff-filter=d --name-only --cached)
git add \$FILES
" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit