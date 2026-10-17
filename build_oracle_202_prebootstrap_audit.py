"""ORACLE202: Read-only pre-bootstrap selection audit."""
import argparse
import ast
import hashlib
import inspect
import json
import re
import textwrap
from pathlib import Path

OUT = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE202_PREBOOTSTRAP_AUDIT.json"
)


def inspect_function(fn):
    source = textwrap.dedent(inspect.getsource(fn))
    tree = ast.parse(source)

    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = ast.unparse(node.func)
        if name not in calls:
            calls.append(name)

    return source, calls


def test():
    def sample(rows):
        return rows[:4]

    source, calls = inspect_function(sample)

    assert "return rows[:4]" in source
    assert ast.parse(source)
    assert calls == []

    def nested(x):
        return len(x)

    source2, calls2 = inspect_function(nested)
    assert "len" in calls2
    assert ast.parse(source2)

    print("[TEST PASS] ORACLE202 nested source dedentation")
    print("[TEST PASS] ORACLE202 AST call extraction")
    print("[SCOPE] static audit only; broadcast=FALSE")


def run():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze,
        runtime as r,
    )

    freeze.freeze()

    fn = r.q25.prepare_once
    source, calls = inspect_function(fn)

    markers = []
    for number, line in enumerate(source.splitlines(), 1):
        if re.search(
            r"limit|top|rank|sort|filter|pair|warm|"
            r"ready|select|slice|budget|return|break",
            line,
            re.IGNORECASE,
        ):
            markers.append(number)

    report = {
        "build": "ORACLE202",
        "status": "STATIC_SOURCE_AUDIT",
        "function": fn.__module__ + "." + fn.__name__,
        "source_sha256": hashlib.sha256(
            source.encode("utf-8")
        ).hexdigest(),
        "source_lines": len(source.splitlines()),
        "called_functions": calls,
        "selection_related_lines": markers,
        "executor_modified": False,
        "signing": False,
        "broadcast": False,
        "profit_certified": False,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print("========== ORACLE202 PREPARE_ONCE SOURCE ==========")
    print(source)

    print("========== ORACLE202 CALL CHAIN ==========")
    for name in calls:
        print("[CALL]", name)

    print(
        "[ORACLE202_SOURCE] lines=%d selection_lines=%s"
        % (len(source.splitlines()), markers)
    )
    print("[REPORT]", OUT)

    freeze.freeze()

    print(
        "[ORACLE202_PASS] "
        "executor_unchanged=TRUE "
        "signing=FALSE broadcast=FALSE"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()

    if args.test:
        test()
    else:
        run()