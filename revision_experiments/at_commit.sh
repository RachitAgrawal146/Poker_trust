#!/usr/bin/env bash
# Run a simulation command with the code of an earlier commit, writing the
# database where the current workflow expects it.
#
# usage: bash revision_experiments/at_commit.sh SHA CMD... --db out/NAME.sqlite
# The commit is checked out in a separate worktree; a relative --db path is
# made absolute against the current directory, so outputs land in ./out/.
set -euo pipefail
SHA="$1"; shift
HERE="$(pwd)"
WT="$(mktemp -d)/code"
git fetch -q --depth=1 origin "$SHA"
git worktree add -q --detach "$WT" FETCH_HEAD
args=()
prev=""
for a in "$@"; do
  if [ "$prev" = "--db" ] || [ "$prev" = "--trajectories" ] || [ "$prev" = "--optlog" ]; then
    case "$a" in /*) ;; *) a="$HERE/$a" ;; esac
  fi
  args+=("$a"); prev="$a"
done
cd "$WT"
echo "running at $(git rev-parse HEAD): ${args[*]}"
"${args[@]}"
