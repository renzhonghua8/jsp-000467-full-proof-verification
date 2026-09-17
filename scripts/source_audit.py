#!/usr/bin/env python3
"""Audit the entire local source closure of the pinned Erdős 577 proof.

Only source hashes and structural findings are emitted, never upstream text.
This is a source audit, not a replacement for Lean kernel or axiom checking.
Python 3.9+ is sufficient; no third-party packages are needed.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT_MODULE = "ErdosProblems.Erdos577"
FORBIDDEN = frozenset(
    {
        "sorry", "admit", "axiom", "native_decide", "unsafe", "opaque",
        "implemented_by", "extern", "ofReduceBool", "trustCompiler", "sorryAx",
        "set_option", "syntax", "macro", "macro_rules", "elab", "elab_rules",
        "initialize", "builtin_initialize", "run_elab", "run_meta", "run_cmd",
        "run_tac",
    }
)
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_']*")
MODULE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*\Z")
IMPORT_LINE = re.compile(r"^[ \t]*(?:(?:public|private)[ \t]+)?import[ \t]+(.+?)[ \t]*$")
BODY_STARTS = frozenset({
    "namespace", "open", "variable", "variables", "section", "noncomputable",
    "universe", "universes", "attribute", "theorem", "lemma", "private",
    "protected", "def", "abbrev", "inductive", "structure", "class",
    "instance", "example", "end", "set_option",
})


class AuditError(Exception):
    """A source cannot be safely analyzed by this deliberately narrow audit."""


def mask_comments_and_strings(source):
    """Mask Lean nested comments and strings while preserving line positions."""
    chars = list(source)
    i = 0
    length = len(source)

    def blank(start, end):
        for pos in range(start, end):
            if chars[pos] not in "\r\n":
                chars[pos] = " "

    while i < length:
        if source.startswith("--", i):
            end = source.find("\n", i)
            end = length if end < 0 else end
            blank(i, end)
            i = end
        elif source.startswith("/-", i):
            start, depth = i, 1
            i += 2
            while i < length and depth:
                if source.startswith("/-", i):
                    depth += 1
                    i += 2
                elif source.startswith("-/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise AuditError("Unterminated block comment")
            blank(start, i)
        elif source[i] == '"':
            if i and source[i - 1] == "!":
                raise AuditError("Interpolated strings are unsupported because they can contain code")
            start = i
            i += 1
            while i < length:
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise AuditError("Unterminated string literal")
            blank(start, min(i, length))
        else:
            i += 1
    return "".join(chars)


def analyze_source(source):
    code = mask_comments_and_strings(source)
    imports = []
    forbidden = []
    import_token_lines = []
    parsed_import_lines = []
    in_header = True
    for lineno, line in enumerate(code.splitlines(), 1):
        tokens = list(IDENTIFIER.finditer(line))
        for token in tokens:
            word = token.group()
            if word in FORBIDDEN:
                forbidden.append({"token": word, "line": lineno, "column": token.start() + 1})
            if word == "import":
                import_token_lines.append(lineno)
        match = IMPORT_LINE.fullmatch(line)
        if match:
            if not in_header:
                raise AuditError("Import found after the module header on line {}".format(lineno))
            names = match.group(1).split()
            if not names or not all(MODULE_NAME.fullmatch(name) for name in names):
                raise AuditError("Unsupported import syntax on line {}".format(lineno))
            imports.extend(names)
            parsed_import_lines.append(lineno)
        elif line.strip() and in_header:
            first = tokens[0].group() if tokens else ""
            if first not in BODY_STARTS and first not in FORBIDDEN and not line.lstrip().startswith("@["):
                raise AuditError("Unsupported header or multiline import on line {}".format(lineno))
            in_header = False
    if import_token_lines != parsed_import_lines:
        raise AuditError("Imports must use conventional complete, single-line declarations")
    return imports, forbidden


def audit(project_root):
    nodes = {}
    errors = []
    external_imports = set()
    visiting = []
    finished = set()
    if (project_root / "Mathlib.lean").exists() or (project_root / "Mathlib").exists():
        errors.append({"kind": "local_mathlib_shadow", "detail": "Project-local Mathlib sources would shadow the external dependency."})

    def visit(module):
        if module in visiting:
            offset = visiting.index(module)
            errors.append({"kind": "import_cycle", "modules": visiting[offset:] + [module]})
            return
        if module in finished:
            return
        relative = Path(*module.split(".")).with_suffix(".lean")
        path = project_root / relative
        if not path.is_file():
            errors.append({"kind": "missing_source", "module": module, "path": relative.as_posix()})
            finished.add(module)
            return
        try:
            raw = path.read_bytes()
            source = raw.decode("utf-8")
            imports, forbidden = analyze_source(source)
        except (OSError, UnicodeError, AuditError) as exc:
            errors.append({"kind": "unreadable_source", "module": module, "detail": str(exc)})
            finished.add(module)
            return
        nodes[module] = {
            "module": module,
            "path": relative.as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "lines": len(source.splitlines()),
            "imports": imports,
        }
        for finding in forbidden:
            errors.append({"kind": "forbidden_token", "module": module, **finding})
        visiting.append(module)
        for dependency in imports:
            if dependency == "Mathlib" or dependency.startswith("Mathlib."):
                external_imports.add(dependency)
            elif dependency == ROOT_MODULE or dependency.startswith(ROOT_MODULE + "."):
                visit(dependency)
            else:
                errors.append({"kind": "unapproved_import", "module": module, "import": dependency})
        visiting.pop()
        finished.add(module)

    visit(ROOT_MODULE)
    return {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "root_module": ROOT_MODULE,
        "scope": "Every recursively imported local proof source; Mathlib is the only external dependency allowed.",
        "limitations": "Static source audit only. Run Lean compilation, independent kernel checking, and an axiom audit separately.",
        "source_count": len(nodes),
        "total_bytes": sum(node["bytes"] for node in nodes.values()),
        "total_lines": sum(node["lines"] for node in nodes.values()),
        "external_imports": sorted(external_imports),
        "forbidden_tokens": sorted(FORBIDDEN),
        "files": [nodes[module] for module in sorted(nodes)],
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."),
                        help="Directory containing ErdosProblems (the source symlink is allowed).")
    parser.add_argument("--output", type=Path,
                        help="Create a new JSON report file; default is standard output. Existing files are never overwritten.")
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    if not project_root.is_dir():
        parser.error("Project root does not exist: {}".format(project_root))
    report = audit(project_root)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    try:
        if args.output is None:
            sys.stdout.write(payload)
        else:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(payload)
    except OSError as exc:
        print("Cannot write report: {}".format(exc), file=sys.stderr)
        return 2
    print("Source audit {}: {} files; {} errors.".format(
        report["status"], report["source_count"], len(report["errors"])), file=sys.stderr)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
