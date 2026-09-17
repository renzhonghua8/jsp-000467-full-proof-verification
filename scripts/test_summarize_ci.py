#!/usr/bin/env python3
"""Pure-memory tests of CI evidence parsing, NOT mathematical proof evidence.

Every source entry, hash, CI identity, compilation line, kernel-success line,
and axiom report below is an explicitly synthetic fixture. No Lean process,
network request, upstream checkout, or actual verification artifact is used.

Run with the target's scripts directory on the import path:

    PYTHONPATH=/path/to/project/scripts python3 -B test_summarize_ci.py -v

The only project file imported is the Python parser under test. Its source
auditor and subprocess invocation are replaced by strict in-memory mocks.
"""

import argparse
import contextlib
import copy
import hashlib
import io
import json
import subprocess
import sys
import types
import unittest
from unittest.mock import Mock, patch

import summarize_ci as subject


FAKE_NOTICE = "SYNTHETIC UNIT TEST FIXTURE ONLY; NOT PROOF OR CI EVIDENCE"
FAKE_COMMIT = "a" * 40
OTHER_FAKE_COMMIT = "b" * 40
PINNED_UPSTREAM = "8822f7ddef30fadbd92e1c6ab4ed897af356af5e"
LOG_PREFIX = "fake-job\tfake-step\t2000-01-01T00:00:00.0000000Z "
KERNEL_PASS = "PASS: full imported environment kernel replay completed."
AXIOM_PASS = "PASS: requested theorem dependency closures use only the standard axiom allowlist."
AXIOM_METHOD = "direct constant-body traversal; no axiom metadata lookup"
TARGET_NAMES = (
    "Erdos577.erdos_577",
    "Jsp467FullReview.erdos_faudree_full",
    "Jsp467FullReview.erdos_faudree_full_pointwise",
)


class MemoryFile:
    """The subset of Path's read interface used by the parser, with no I/O."""

    def __init__(self, text):
        self.text = text

    def read_bytes(self):
        return self.text.encode("utf-8")

    def read_text(self, *args, **kwargs):
        return self.text


def fake_source_manifest():
    modules = ["ErdosProblems.Erdos577"] + [
        "ErdosProblems.Erdos577.FakeFixture{:04d}".format(i)
        for i in range(1, 851)
    ]
    entries = []
    for module in modules:
        payload = (FAKE_NOTICE + " " + module).encode("utf-8")
        entries.append({
            "module": module,
            "path": module.replace(".", "/") + ".lean",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "lines": 1,
            "imports": ["Mathlib"],
        })
    return {
        "fixture_notice": FAKE_NOTICE,
        "schema_version": 1,
        "status": "pass",
        "root_module": "ErdosProblems.Erdos577",
        "source_count": 851,
        "files": entries,
        "errors": [],
        "external_imports": ["Mathlib"],
    }


def fake_metadata():
    return {
        "fixture_notice": FAKE_NOTICE,
        "status": "completed",
        "conclusion": "success",
        "headSha": FAKE_COMMIT,
        "databaseId": 9000000001,
        "attempt": 3,
        "url": "https://example.invalid/synthetic-unit-test-ci-run",
    }


def fake_axiom_reports():
    return [{
        "fixture_notice": FAKE_NOTICE,
        "theorem": theorem,
        "visitedConstants": 1000,
        "axioms": ["propext", "Classical.choice", "Quot.sound"],
        "disallowedAxioms": [],
        "onlyStandardAxioms": True,
        "exactStandardSet": True,
        "method": AXIOM_METHOD,
    } for theorem in TARGET_NAMES]


def fake_log(source, run, reports):
    lines = [
        FAKE_NOTICE,
        LOG_PREFIX + "CI_IDENTITY run={databaseId} attempt={attempt} commit={headSha}".format(**run),
        LOG_PREFIX + "[command]/usr/bin/git log -1 --format=%H",
        LOG_PREFIX + run["headSha"],
        LOG_PREFIX + "Verified unchanged upstream commit {}.".format(PINNED_UPSTREAM),
    ]
    for i, entry in enumerate(source["files"], 1):
        lines.append(LOG_PREFIX + "✔ [{}/851] Built {} (0ms)".format(i, entry["module"]))
    lines.extend([
        LOG_PREFIX + "Built Jsp467FullReview.Bridge (0ms)",
        LOG_PREFIX + KERNEL_PASS,
        LOG_PREFIX + AXIOM_PASS,
    ])
    lines.extend(LOG_PREFIX + json.dumps(report, separators=(",", ":")) for report in reports)
    return "\n".join(lines) + "\n"


class SummarizeCiSyntheticTests(unittest.TestCase):
    """Parser-only regression tests; all evidence is deliberately fake."""

    def setUp(self):
        self.source = fake_source_manifest()
        self.pinned_audit_result = copy.deepcopy(self.source)
        self.run = fake_metadata()
        self.reports = fake_axiom_reports()
        self.log = fake_log(self.source, self.run, self.reports)
        self.expected_commit = FAKE_COMMIT
        self.stdout = io.StringIO()
        self.subprocess_mock = None
        self.audit_mock = None

    def invoke(self, fetch_error=None):
        args = argparse.Namespace(
            source_audit=MemoryFile(json.dumps(self.source)),
            log=MemoryFile(self.log),
            run_metadata=MemoryFile(json.dumps(self.run)),
            expected_commit=self.expected_commit,
        )
        fake_audit_module = types.ModuleType("source_audit")
        fake_audit_module.audit = Mock(return_value=copy.deepcopy(self.pinned_audit_result))
        self.audit_mock = fake_audit_module.audit
        self.subprocess_mock = Mock(
            return_value=subprocess.CompletedProcess(["FAKE_CHECK_ONLY"], 0),
            side_effect=fetch_error,
        )
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(argparse.ArgumentParser, "parse_args", return_value=args))
            stack.enter_context(patch.dict(sys.modules, {"source_audit": fake_audit_module}))
            stack.enter_context(patch.object(subject.subprocess, "run", self.subprocess_mock))
            # A future parser change cannot accidentally launch a real process
            # or network call while these synthetic tests execute.
            stack.enter_context(patch("subprocess.Popen", side_effect=AssertionError("Real subprocess forbidden in synthetic tests")))
            stack.enter_context(patch("socket.socket", side_effect=AssertionError("Network forbidden in synthetic tests")))
            stack.enter_context(contextlib.redirect_stdout(self.stdout))
            subject.main()
        return json.loads(self.stdout.getvalue())

    def reject(self, message):
        with self.assertRaisesRegex(SystemExit, message):
            self.invoke()
        self.assertEqual(self.stdout.getvalue(), "", "A rejected fixture must emit no success summary")

    def remove_log_lines(self, text):
        self.log = "\n".join(line for line in self.log.splitlines() if text not in line) + "\n"

    def test_positive_complete_851_record_fixture(self):
        result = self.invoke()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["source_modules"], 851)
        self.assertEqual(result["freshly_compiled_source_modules"], 851)
        self.assertEqual(result["ci_run_id"], self.run["databaseId"])
        self.assertEqual(result["ci_run_attempt"], 3)
        self.assertEqual(result["checked_commit"], FAKE_COMMIT)
        self.assertEqual({item["theorem"] for item in result["axiom_reports"]}, set(TARGET_NAMES))
        self.subprocess_mock.assert_called_once()
        self.assertIn("--check-only", self.subprocess_mock.call_args.args[0])
        self.assertTrue(self.subprocess_mock.call_args.kwargs["check"])
        self.audit_mock.assert_called_once()

    def test_reject_empty_manifest(self):
        self.source["files"] = []
        self.source["source_count"] = 0
        self.reject("complete unique 851-module")
        self.subprocess_mock.assert_not_called()

    def test_reject_duplicate_manifest_entry(self):
        self.source["files"][-1] = copy.deepcopy(self.source["files"][0])
        self.reject("complete unique 851-module")

    def test_reject_missing_manifest_module(self):
        self.source["files"].pop()
        self.source["source_count"] = 850
        self.reject("complete unique 851-module")

    def test_reject_wrong_manifest_root(self):
        self.source["root_module"] = "FakeUnrelated.Root"
        self.reject("complete unique 851-module")

    def test_reject_inconsistent_manifest_count(self):
        self.source["source_count"] = 850
        self.reject("complete unique 851-module")

    def test_reject_missing_fresh_compilation_record(self):
        missing = self.source["files"][400]["module"]
        self.remove_log_lines("Built " + missing + " (")
        self.reject("Missing fresh source-build records")

    def test_reject_cancelled_metadata(self):
        self.run["conclusion"] = "cancelled"
        self.reject("CI has not completed successfully")

    def test_reject_failed_metadata(self):
        self.run["conclusion"] = "failure"
        self.reject("CI has not completed successfully")

    def test_reject_in_progress_metadata(self):
        self.run["status"] = "in_progress"
        self.run["conclusion"] = None
        self.reject("CI has not completed successfully")

    def test_reject_wrong_run_id(self):
        self.run["databaseId"] += 1
        self.reject("not bound to this exact run")

    def test_reject_wrong_run_attempt(self):
        self.run["attempt"] += 1
        self.reject("not bound to this exact run")

    def test_reject_metadata_commit_mismatch(self):
        self.run["headSha"] = OTHER_FAKE_COMMIT
        self.reject("CI commit mismatch")

    def test_reject_identity_commit_mismatch(self):
        self.log = self.log.replace("commit=" + FAKE_COMMIT, "commit=" + OTHER_FAKE_COMMIT)
        self.reject("not bound to this exact run")

    def test_reject_checkout_commit_mismatch(self):
        self.log = self.log.replace(LOG_PREFIX + FAKE_COMMIT + "\n", LOG_PREFIX + OTHER_FAKE_COMMIT + "\n")
        self.reject("checkout record does not match")

    def test_reject_missing_checkout_record(self):
        self.remove_log_lines("git log -1 --format=%H")
        self.reject("checkout record does not match")

    def test_reject_missing_pinned_upstream_verification(self):
        self.remove_log_lines("Verified unchanged upstream commit")
        self.reject("Pinned upstream checkout verification is absent")

    def test_reject_failed_source_audit(self):
        self.source["status"] = "fail"
        self.source["errors"] = [{"kind": "synthetic_error", "fixture_notice": FAKE_NOTICE}]
        self.reject("Source audit failed")

    def test_reject_report_different_from_mock_pinned_source_audit(self):
        self.source["files"][0]["sha256"] = "f" * 64
        self.reject("source report does not match the pinned checkout")
        self.audit_mock.assert_called_once()

    def test_reject_checkout_check_only_failure(self):
        error = subprocess.CalledProcessError(1, ["FAKE_CHECK_ONLY"])
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke(fetch_error=error)
        self.assertEqual(self.stdout.getvalue(), "")
        self.audit_mock.assert_not_called()

    def test_reject_missing_bridge_compilation(self):
        self.remove_log_lines("Built Jsp467FullReview.Bridge (")
        self.reject("Bridge was not freshly compiled")

    def test_reject_missing_kernel_success(self):
        self.remove_log_lines(KERNEL_PASS)
        self.reject("Full kernel replay success is absent")

    def test_reject_missing_direct_axiom_success(self):
        self.remove_log_lines(AXIOM_PASS)
        self.reject("Direct axiom closure success is absent")

    def test_reject_missing_endpoint_axiom_report(self):
        self.reports.pop()
        self.log = fake_log(self.source, self.run, self.reports)
        self.reject("Missing endpoint axiom reports")

    def test_reject_malformed_endpoint_json(self):
        line = LOG_PREFIX + json.dumps(self.reports[-1], separators=(",", ":"))
        self.log = self.log.replace(line, LOG_PREFIX + '{"theorem": "SYNTHETIC MALFORMED JSON"')
        self.reject("Missing endpoint axiom reports")

    def test_reject_axiom_report_marked_failed(self):
        self.reports[0]["onlyStandardAxioms"] = False
        self.log = fake_log(self.source, self.run, self.reports)
        self.reject("A theorem axiom check failed")

    def test_reject_disallowed_axiom_report(self):
        self.reports[0]["disallowedAxioms"] = ["SyntheticTest.fakeAxiom"]
        self.log = fake_log(self.source, self.run, self.reports)
        self.reject("A theorem axiom check failed")

    def test_reject_custom_axiom_even_when_boolean_claims_pass(self):
        self.reports[0]["axioms"].append("SyntheticTest.fakeAxiom")
        self.log = fake_log(self.source, self.run, self.reports)
        self.reject("Unexpected theorem axiom")

    def test_reject_wrong_axiom_inspection_method(self):
        self.reports[0]["method"] = "SYNTHETIC UNTRUSTED METADATA ONLY"
        self.log = fake_log(self.source, self.run, self.reports)
        self.reject("Unexpected axiom inspection method")


if __name__ == "__main__":
    print(FAKE_NOTICE, file=sys.stderr)
    unittest.main()
