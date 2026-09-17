#!/usr/bin/env python3
"""Build one of six deterministic topological stages of the complete proof.

Reads and validates the current 851-module source closure with source_audit.
Each real invocation executes exactly one `lake build` command. `--dry-run`
emits the selected module targets and counts as JSON and never invokes Lake.
Python 3.9+; standard library only.
"""

import argparse
import hashlib
import heapq
import json
import subprocess
import sys
from pathlib import Path

import source_audit


STAGE_COUNT = 6
EXPECTED_MODULE_COUNT = 851


class StageError(Exception):
    """The audited source graph cannot safely be staged."""


def topological_order(report):
    """Dependencies precede dependents; lexical ties make the order stable."""
    if report.get("status") != "pass" or report.get("errors"):
        raise StageError("Source audit did not pass; refusing to build a staged closure.")
    records = report.get("files", [])
    nodes = {record["module"]: record for record in records}
    if len(nodes) != len(records):
        raise StageError("Duplicate modules in the source audit report.")
    if len(nodes) != EXPECTED_MODULE_COUNT:
        raise StageError(
            "Expected the pinned {}-module proof closure, found {}."
            .format(EXPECTED_MODULE_COUNT, len(nodes))
        )
    root = report.get("root_module")
    if root != source_audit.ROOT_MODULE or root not in nodes:
        raise StageError("The source audit does not identify the expected complete theorem.")

    dependencies = {}
    dependents = {module: [] for module in nodes}
    for module, record in nodes.items():
        local = set()
        for dependency in record["imports"]:
            if dependency in nodes:
                local.add(dependency)
            elif dependency == "Mathlib" or dependency.startswith("Mathlib."):
                continue
            else:
                raise StageError("Unresolved local dependency: {} -> {}".format(module, dependency))
        dependencies[module] = local
        for dependency in local:
            dependents[dependency].append(module)

    remaining = {module: len(deps) for module, deps in dependencies.items()}
    ready = [module for module, count in remaining.items() if count == 0]
    heapq.heapify(ready)
    ordered = []
    while ready:
        module = heapq.heappop(ready)
        ordered.append(module)
        for dependent in sorted(dependents[module]):
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                heapq.heappush(ready, dependent)
    if len(ordered) != len(nodes):
        raise StageError("The proof imports contain a dependency cycle.")
    if ordered[-1] != root:
        raise StageError("Unexpected graph: the complete theorem is not the final target.")

    position = {module: i for i, module in enumerate(ordered)}
    for module, deps in dependencies.items():
        if any(position[dependency] >= position[module] for dependency in deps):
            raise StageError("Internal error: generated order is not topological.")
    return ordered, dependencies


def stage_plan(report, stage, lake):
    ordered, dependencies = topological_order(report)
    quotient, remainder = divmod(len(ordered), STAGE_COUNT)
    counts = [quotient + (i < remainder) for i in range(STAGE_COUNT)]
    offset = sum(counts[:stage - 1])
    selected = ordered[offset:offset + counts[stage - 1]]
    index = {module: i for i, module in enumerate(ordered)}
    previous_dependencies = sorted({
        dependency
        for module in selected
        for dependency in dependencies[module]
        if index[dependency] < offset
    })

    # `:lean` names a source-file facet in Lake 4.33; it does not compile.
    # `+` disambiguates modules and `:leanArts` builds their Lean artifacts.
    targets = ["+{}:leanArts".format(module) for module in selected]
    return {
        "schema_version": 1,
        "root_module": report["root_module"],
        "stage": stage,
        "stage_count": STAGE_COUNT,
        "total_module_count": len(ordered),
        "all_stage_module_counts": counts,
        "stage_module_count": len(selected),
        "topological_start_index_1based": offset + 1,
        "topological_end_index_1based": offset + len(selected),
        "topological_order_sha256": hashlib.sha256(
            ("\n".join(ordered) + "\n").encode("utf-8")
        ).hexdigest(),
        "source_closure_sha256": hashlib.sha256(
            json.dumps(
                [(record["module"], record["sha256"]) for record in report["files"]],
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        "previous_stage_direct_dependency_count": len(previous_dependencies),
        "modules": selected,
        "targets": targets,
        "command": [lake, "build"] + targets,
        "note": "Run stages 1 through 6 in order and preserve build artifacts between stages. Lake may rebuild any missing earlier dependency.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."),
                        help="Project containing the current ErdosProblems source tree.")
    parser.add_argument("--stage", type=int, required=True, choices=range(1, STAGE_COUNT + 1))
    parser.add_argument("--lake", default="lake",
                        help="Lake executable (path or PATH name); never interpreted as shell text.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print JSON targets/counts without invoking Lake or writing files.")
    args = parser.parse_args(argv)
    project_root = args.project_root.resolve()
    if not project_root.is_dir():
        parser.error("Project directory does not exist: {}".format(project_root))
    try:
        report = source_audit.audit(project_root)
        plan = stage_plan(report, args.stage, args.lake)
    except (OSError, ValueError, KeyError, StageError) as exc:
        print("Stage planning failed: {}".format(exc), file=sys.stderr)
        return 2

    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    print(
        "Building stage {stage}/{stage_count}: {stage_module_count} explicit modules "
        "(topological positions {topological_start_index_1based}–{topological_end_index_1based} "
        "of {total_module_count}); order SHA-256 {topological_order_sha256}.".format(**plan),
        flush=True,
    )
    try:
        completed = subprocess.run(plan["command"], cwd=str(project_root), check=False)
    except OSError as exc:
        print("Could not execute Lake: {}".format(exc), file=sys.stderr)
        return 2
    if completed.returncode == 0:
        print("Stage {}/{} completed successfully.".format(args.stage, STAGE_COUNT), flush=True)
    else:
        print("Stage {}/{} failed (Lake return code {}).".format(
            args.stage, STAGE_COUNT, completed.returncode), file=sys.stderr, flush=True)
    return completed.returncode if completed.returncode >= 0 else 128 - completed.returncode


if __name__ == "__main__":
    sys.exit(main())
