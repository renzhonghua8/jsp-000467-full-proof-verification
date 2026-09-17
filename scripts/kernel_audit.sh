#!/usr/bin/env bash
set -euo pipefail

# Recheck existing artifacts only. This script never invokes `lake build`.
# Usage: bash kernel_audit.sh PROJECT TOOLCHAIN_BIN REPORT_DIRECTORY [MODULE [THEOREM...]]
if (( $# < 3 )); then
  printf '%s\n' 'Usage: bash kernel_audit.sh PROJECT TOOLCHAIN_BIN REPORT_DIRECTORY [MODULE [THEOREM...]]' >&2
  exit 2
fi

audit_project=$(cd "$1" && pwd -P)
audit_toolchain_bin=$(cd "$2" && pwd -P)
audit_report=$3
shift 3
audit_module=${1:-Jsp467FullReview.Bridge}
if (( $# > 0 )); then shift; fi
if (( $# == 0 )); then
  set -- Erdos577.erdos_577 Jsp467FullReview.erdos_faudree_full Jsp467FullReview.erdos_faudree_full_pointwise
fi
audit_script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
audit_checker_source="$audit_toolchain_bin/../src/lean/LeanChecker.lean"

for audit_exe in lean lake leanchecker; do
  if [[ ! -x "$audit_toolchain_bin/$audit_exe" ]]; then
    printf 'Missing executable: %s\n' "$audit_toolchain_bin/$audit_exe" >&2
    exit 2
  fi
done
if [[ ! -f "$audit_project/lean-toolchain" || ! -f "$audit_project/lake-manifest.json" ]]; then
  printf '%s\n' 'The project must already have its pinned toolchain and dependency manifest.' >&2
  exit 2
fi
if [[ ! -f "$audit_script_dir/AxiomClosure.lean" || ! -f "$audit_checker_source" ]]; then
  printf '%s\n' 'The direct axiom inspector and the installed checker source are required.' >&2
  exit 2
fi
if ! grep -q 'let fresh := "--fresh"' "$audit_checker_source"; then
  printf '%s\n' 'This checker version was not recognized: refusing to guess flag semantics.' >&2
  exit 2
fi

if [[ -e "$audit_report" || -L "$audit_report" ]]; then
  printf 'Report path already exists; choose a new directory: %s\n' "$audit_report" >&2
  exit 2
fi
mkdir -p "$(dirname "$audit_report")"
mkdir "$audit_report"
audit_report=$(cd "$audit_report" && pwd -P)
export PATH="$audit_toolchain_bin:$PATH"
export LEAN_NUM_THREADS=${LEAN_NUM_THREADS:-1}
cd "$audit_project"

audit_version=$("$audit_toolchain_bin/lean" --version)
audit_pin=$(tr -d '\r\n' < lean-toolchain)
case "$audit_pin" in
  leanprover/lean4:v4.33.0) [[ "$audit_version" == *'version 4.33.0'* ]] ;;
  leanprover/lean4:v4.34.0) [[ "$audit_version" == *'version 4.34.0'* ]] ;;
  *) printf 'Unsupported project toolchain: %s\n' "$audit_pin" >&2; exit 2 ;;
esac

{
  printf 'Project: %s\n' "$audit_project"
  printf 'Toolchain pin: %s\n' "$audit_pin"
  printf 'Toolchain executable: %s\n' "$audit_toolchain_bin/lean"
  printf '%s\n' "$audit_version"
  printf 'Module: %s\n' "$audit_module"
  printf 'Theorem: %s\n' "$@"
  printf 'Mode: --fresh (all loaded transitive imports replayed into an empty kernel environment)\n'
  printf 'Threads: %s\n' "$LEAN_NUM_THREADS"
  printf 'Started UTC: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$audit_report/configuration.txt"

# This traverses the actual checked constant bodies, not exported axiom summaries.
# Run it before the expensive replay so its independent evidence survives a
# replay timeout. It does not replace the required empty-environment replay.
printf 'Starting direct axiom-body audit UTC: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
"$audit_toolchain_bin/lake" env "$audit_toolchain_bin/lean" --run \
  "$audit_script_dir/AxiomClosure.lean" "$audit_module" "$@" \
  2>&1 | tee "$audit_report/axiom-closure.jsonl"
printf 'Direct axiom-body audit finished UTC: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Do not pass --help or -r: these unknown flags are silently ignored in 4.33/4.34.
# A precise module avoids the package-name/default-prefix heuristic.
# On Linux, line-buffer the checker output so its startup message is visible
# even if the process is later terminated. This changes no checker arguments.
printf 'Starting full fresh kernel replay UTC: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if command -v stdbuf >/dev/null 2>&1; then
  "$audit_toolchain_bin/lake" env stdbuf -oL -eL \
    "$audit_toolchain_bin/leanchecker" --fresh --verbose "$audit_module" \
    2>&1 | tee "$audit_report/kernel-fresh.log"
else
  "$audit_toolchain_bin/lake" env "$audit_toolchain_bin/leanchecker" --fresh --verbose "$audit_module" \
    2>&1 | tee "$audit_report/kernel-fresh.log"
fi

{
  printf 'PASS: full imported environment kernel replay completed.\n'
  printf 'PASS: requested theorem dependency closures use only the standard axiom allowlist.\n'
  printf 'Axiom details: axiom-closure.jsonl\n'
  printf 'Finished UTC: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$audit_report/result.txt"
