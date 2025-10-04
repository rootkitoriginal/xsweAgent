#!/usr/bin/env bash
# husky - installation helper script
# copied minimal shim to make hooks portable inside repo
# (normally created by `husky install`)

HUSKY_SKIP_TESTS=1

if [ -z "$HUSKY_GIT_PARAMS" ]; then
  export HUSKY_GIT_PARAMS="$*"
fi

# find project root
ROOT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
HUSKY_DIR="$ROOT_DIR/.husky"

# source hook helper if exists
if [ -f "$HUSKY_DIR/_/husky.sh" ]; then
  source "$HUSKY_DIR/_/husky.sh"
fi
