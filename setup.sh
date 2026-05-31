#!/bin/sh
set -eu

if command -v zero >/dev/null 2>&1; then
  zero_bin="$(command -v zero)"
elif [ -n "${HOME:-}" ] && [ -x "$HOME/.zero/bin/zero" ]; then
  zero_bin="$HOME/.zero/bin/zero"
else
  printf 'setup.sh: zero is required\n' >&2
  exit 1
fi

if [ -n "${ZKG_SOURCE:-}" ]; then
  source_dir="$ZKG_SOURCE"
elif [ -f zero.json ] && [ -d src/zkg ]; then
  source_dir="."
elif [ -d .zkg/src ]; then
  source_dir=".zkg"
elif [ -n "${ZKG_HOME:-}" ] && [ -d "$ZKG_HOME/src" ]; then
  source_dir="$ZKG_HOME"
elif [ -n "${HOME:-}" ] && [ -d "$HOME/.zkg/src" ]; then
  source_dir="$HOME/.zkg"
else
  printf 'setup.sh: source package not found; run from the zkg checkout or set ZKG_SOURCE\n' >&2
  exit 1
fi

exec "$zero_bin" run "$source_dir" -- "$@"
