"""ORACLE210: Offline, source-only quote failure audit."""
import argparse
import ast
import hashlib
import inspect
import json
import textwrap
from pathlib import Path

OUT = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE210_OFFLINE_QUOTE_AUDIT.json"
)


def analyze(fn):
    source = textwrap.dedent(inspect.getsource(fn))
    tree = ast.parse(source)
    lines = source.splitlines()

    calls = sorted({
        ast.unparse(n.func)
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
    })

    raises = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Raise):
            raises.append({
                "line": n.lineno,
                "expression": ast.unparse(n.exc)
                if n.exc is not None else "RERAISE",
            })

    keywords = (
        "raise", "except", "snapshot", "warm",
        "quote", "price", "reserve", "sdk",
        "array", "liquid", "state", "return",
    )

    relevant = [
        {"line": i, "source": line.rstrip()}
        for i, line in enumerate(lines, 1)
        if any(x in line.lower() for x in keywords)
    ]

    return {
        "function": fn.__module__ + "." + fn.__name__,
        "file": Path(inspect.getfile(fn)).name,
        "sha256": hashlib.sha256(source.encode()).hexdigest(),
        "source_lines": len(lines),
        "calls": calls,
        "raises": sorted(raises, key=lambda x: x["line"]),
        "relevant_source": relevant,
    }


def test():
    def fixture(value):
        if value is None:
            raise RuntimeError("MISSING_STATE")
        return value

    result = analyze(fixture)
    assert result["raises"][0]["line"] > 0
    assert "RuntimeError" in result["raises"][0]["expression"]
    assert "fixture" in result["function"]
    print("[ORACLE210_TEST_PASS] source_ast=TRUE")


def run():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze,
        runtime as r,
    )

    freeze.freeze()

    fn = r.q18.exact_snapshot_opportunities
    result = analyze(fn)

    report = {
        "build": "ORACLE210",
        "status": "OFFLINE_SOURCE_ONLY",
        "quote_function": result,
        "rpc": False,
        "wallet_credentials_loaded": False,
        "signing": False,
        "broadcast": False,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("[ORACLE210_FUNCTION]", result["function"])
    print("[ORACLE210_SOURCE_FILE]", result["file"])

    print("========== QUOTE SOURCE ==========")
    for row in result["relevant_source"]:
        print("%04d %s" % (row["line"], row["source"]))

    print("========== CALLED FUNCTIONS ==========")
    for call in result["calls"]:
        print("[CALL]", call)

    print("========== EXPLICIT EXCEPTIONS ==========")
    for item in result["raises"]:
        print("[RAISE]", item["line"], item["expression"])

    print("[REPORT]", OUT)

    freeze.freeze()
    print(
        "[ORACLE210_PASS] execution_unchanged=TRUE "
        "rpc=FALSE broadcast=FALSE"
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