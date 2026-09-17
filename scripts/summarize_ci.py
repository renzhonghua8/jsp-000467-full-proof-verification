#!/usr/bin/env python3
"""Validate completed CI evidence; print a compact JSON record or fail closed."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-audit", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--run-metadata", required=True, type=Path)
    parser.add_argument("--expected-commit", required=True)
    args = parser.parse_args()
    source_raw = args.source_audit.read_bytes()
    source = json.loads(source_raw)
    log_raw = args.log.read_bytes()
    log = log_raw.decode("utf-8-sig")
    run = json.loads(args.run_metadata.read_text())
    require(run["status"] == "completed" and run["conclusion"] == "success",
            "CI has not completed successfully")
    require(run["headSha"] == args.expected_commit, "CI commit mismatch")
    marker = (f"CI_IDENTITY run={run['databaseId']} attempt={run['attempt']} "
              f"commit={run['headSha']}")
    require(re.search(r"Z " + re.escape(marker) + r"\s*$", log, re.MULTILINE),
            "The log is not bound to this exact run, attempt, and commit")
    require(re.search(r"git log -1 --format=%H\s*\n[^\n]*Z " +
                      re.escape(args.expected_commit) + r"\s*$", log, re.MULTILINE),
            "The checkout record does not match the claimed commit")
    require("Verified unchanged upstream commit 8822f7ddef30fadbd92e1c6ab4ed897af356af5e." in log,
            "Pinned upstream checkout verification is absent")
    require(source["status"] == "pass" and not source["errors"], "Source audit failed")
    expected = {item["module"] for item in source["files"]}
    require(source.get("root_module") == "ErdosProblems.Erdos577" and
            source.get("source_count") == len(source["files"]) == len(expected) == 851,
            "Expected the complete unique 851-module source closure")
    project = Path(__file__).resolve().parent.parent
    subprocess.run(["bash", str(project / "scripts/fetch_upstream.sh"),
                    "--check-only", str(project)], check=True, stdout=subprocess.DEVNULL)
    from source_audit import audit
    require(source == audit(project), "The source report does not match the pinned checkout")
    compiled = set(re.findall(r"Built (ErdosProblems\.Erdos577(?:\.[A-Za-z0-9_]+)*) \(", log))
    require(expected <= compiled,
            "Missing fresh source-build records: " + ", ".join(sorted(expected - compiled)))
    require("Built Jsp467FullReview.Bridge (" in log, "Bridge was not freshly compiled")
    require("PASS: full imported environment kernel replay completed." in log,
            "Full kernel replay success is absent")
    require("PASS: requested theorem dependency closures use only the standard axiom allowlist." in log,
            "Direct axiom closure success is absent")
    target_names = {
        "Erdos577.erdos_577",
        "Jsp467FullReview.erdos_faudree_full",
        "Jsp467FullReview.erdos_faudree_full_pointwise",
    }
    reports = {}
    for line in log.splitlines():
        start = line.find('{"')
        if start < 0:
            continue
        try:
            item = json.loads(line[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and item.get("theorem") in target_names:
            reports[item["theorem"]] = item
    require(set(reports) == target_names, "Missing endpoint axiom reports")
    allowed = {"propext", "Classical.choice", "Quot.sound"}
    for report in reports.values():
        require(report.get("onlyStandardAxioms") is True and not report.get("disallowedAxioms"),
                "A theorem axiom check failed")
        require(set(report["axioms"]) <= allowed, "Unexpected theorem axiom")
        require(report.get("method") == "direct constant-body traversal; no axiom metadata lookup",
                "Unexpected axiom inspection method")
    print(json.dumps({
        "status": "pass",
        "ci_url": run["url"],
        "ci_run_id": run["databaseId"],
        "ci_run_attempt": run["attempt"],
        "checked_commit": run["headSha"],
        "upstream_commit": "8822f7ddef30fadbd92e1c6ab4ed897af356af5e",
        "source_modules": len(expected),
        "freshly_compiled_source_modules": len(expected & compiled),
        "source_audit_sha256": hashlib.sha256(source_raw).hexdigest(),
        "ci_log_sha256": hashlib.sha256(log_raw).hexdigest(),
        "kernel_replay": "all transitive imports replayed into an empty Lean kernel environment",
        "axiom_reports": [reports[name] for name in sorted(reports)],
        "boundary": "Mathlib caches provide stored terms for replay; no claim of compiling Mathlib from source or of a separately implemented kernel",
    }, indent=2))


if __name__ == "__main__":
    main()
