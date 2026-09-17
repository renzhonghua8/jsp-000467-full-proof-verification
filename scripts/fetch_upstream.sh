#!/usr/bin/env bash
# Download an unchanged, pinned upstream proof for local verification only.
# This script grants no license to, and does not redistribute, upstream code.
set -euo pipefail

readonly UPSTREAM_URL='https://github.com/plby/lean-proofs.git'
readonly UPSTREAM_COMMIT='8822f7ddef30fadbd92e1c6ab4ed897af356af5e'

usage() {
  printf 'Usage: bash fetch_upstream.sh [--check-only] [PROJECT_ROOT]\n' >&2
  printf 'PROJECT_ROOT defaults to the current directory and must already exist.\n' >&2
}

fail() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

check_only=false
if [[ "${1-}" == '--check-only' ]]; then
  check_only=true
  shift
fi
if [[ "${1-}" == '--help' || "${1-}" == '-h' ]]; then
  usage
  exit 0
fi
[[ $# -le 1 ]] || { usage; exit 2; }
project_input="${1:-.}"
[[ -d "$project_input" ]] || fail "Project directory does not exist: $project_input"
project_root="$(cd -- "$project_input" && pwd -P)"
readonly project_root
readonly cache_dir="$project_root/.upstream"
readonly checkout="$cache_dir/lean-proofs"
readonly link_path="$project_root/ErdosProblems"
readonly relative_link='.upstream/lean-proofs/src/latest/ErdosProblems'

command -v git >/dev/null 2>&1 || fail 'git is required.'
[[ ! -L "$cache_dir" ]] || fail "Refusing a symlinked cache directory: $cache_dir"
[[ ! -L "$checkout" ]] || fail "Refusing a symlinked checkout directory: $checkout"

# Existing source trees are inspected only: no fetch, checkout, reset, or clean.
verify_checkout() {
  [[ -d "$checkout/.git" ]] || fail "Existing path is not a standalone Git checkout: $checkout"
  local git_root head dirty
  git_root="$(git -C "$checkout" rev-parse --show-toplevel)" || fail 'Cannot inspect the upstream checkout.'
  [[ "$git_root" == "$checkout" ]] || fail "Unexpected Git root: $git_root"
  head="$(git -C "$checkout" rev-parse HEAD)" || fail 'Cannot read upstream HEAD.'
  [[ "$head" == "$UPSTREAM_COMMIT" ]] || fail "Existing upstream HEAD is $head; expected $UPSTREAM_COMMIT. Existing data was not changed."
  dirty="$(git -C "$checkout" status --porcelain=v1 --untracked-files=all)" || fail 'Cannot inspect upstream status.'
  [[ -z "$dirty" ]] || fail 'Upstream checkout has local changes or untracked files. Existing data was not changed.'
  [[ -f "$checkout/src/latest/ErdosProblems/Erdos577.lean" ]] || fail 'The pinned main proof is missing.'
  [[ -d "$checkout/src/latest/ErdosProblems/Erdos577" ]] || fail 'The pinned support directory is missing.'
}

if [[ -e "$checkout" ]]; then
  verify_checkout
else
  "$check_only" && fail "No upstream checkout at $checkout; --check-only will not download it."
  [[ ! -e "$cache_dir" || -d "$cache_dir" ]] || fail "Cache path is not a directory: $cache_dir"
  mkdir -p -- "$cache_dir"
  # mkdir atomically reserves a new path; it fails if another process created it.
  mkdir -- "$checkout" || fail "Checkout path already exists: $checkout"
  printf 'Fetching upstream commit %s for local verification.\n' "$UPSTREAM_COMMIT" >&2
  printf 'If interrupted, the incomplete checkout is preserved; no existing files will be reset.\n' >&2
  git -C "$checkout" init --quiet
  git -C "$checkout" remote add origin "$UPSTREAM_URL"
  git -C "$checkout" -c protocol.version=2 fetch --filter=blob:none --depth=1 origin "$UPSTREAM_COMMIT"
  git -C "$checkout" sparse-checkout set --no-cone \
    /AGENTS.md \
    /src/latest/LICENSE \
    /src/latest/lean-toolchain \
    /src/latest/lake-manifest.json \
    /src/latest/ErdosProblems/Erdos577.lean \
    /src/latest/ErdosProblems/Erdos577/ \
    /tex/577.tex
  git -C "$checkout" -c advice.detachedHead=false checkout --detach "$UPSTREAM_COMMIT"
  verify_checkout
fi

if [[ -L "$link_path" ]]; then
  resolved_link="$(cd -- "$link_path" && pwd -P)" || fail "Existing source link is broken: $link_path"
  [[ "$resolved_link" == "$checkout/src/latest/ErdosProblems" ]] || fail "Existing source link points elsewhere: $link_path"
elif [[ -e "$link_path" ]]; then
  fail "Refusing to replace existing source path: $link_path"
elif "$check_only"; then
  fail "Source link is missing: $link_path; --check-only will not create it."
else
  ln -s -- "$relative_link" "$link_path"
fi

printf 'Verified unchanged upstream commit %s.\n' "$UPSTREAM_COMMIT"
printf 'Source link: %s\n' "$link_path"
