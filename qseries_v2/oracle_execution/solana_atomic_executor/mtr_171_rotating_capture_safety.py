
"""MTR-171: physical rotating runtime safety gate. No execution."""

import ast
import inspect
import json
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt

REVISION = "MTR171_ROTATING_SAFETY_GATE"

BLOCKED = {
    "signed_tx", "keypair", "send", "sendTransaction",
    "send_transaction", "compile_current",
    "simulate_current", "fast_live_attack",
    "_execute_route_once", "_live_010_armed",
}

def calls_of(fn):
    tree = ast.parse(inspect.getsource(fn))
    return sorted({
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    })

def inspect_runtime():
    run = rt.run
    price = rt.canonical_price
    rotating = getattr(rt, "serve_rotating", None)

    if not callable(rotating):
        raise RuntimeError("SERVE_ROTATING_MISSING")

    run_names = set(run.__code__.co_names)
    price_names = set(price.__code__.co_names)
    rotating_names = set(rotating.__code__.co_names)

    if "serve_rotating" not in run_names:
        raise RuntimeError("RUN_NOT_CONNECTED_TO_ROTATING")

    if "fast_live_attack" not in price_names:
        raise RuntimeError("PRICE_CALLBACK_CHANGED")

    if "canonical_price" not in run_names:
        raise RuntimeError("PRICE_LANE_BINDING_MISSING")

    functions = {
        "run": run,
        "serve_rotating": rotating,
        "canonical_price": price,
    }

    report = {
        "revision": REVISION,
        "source": str(Path(run.__code__.co_filename)),
        "functions": {},
        "startup_execution_proven_safe": False,
        "live_capture_authorized": False,
        "private_key_access_authorized": False,
        "signing_authorized": False,
        "broadcast_authorized": False,
    }

    for name, fn in functions.items():
        names = sorted(set(fn.__code__.co_names))
        calls = calls_of(fn)

        report["functions"][name] = {
            "line": fn.__code__.co_firstlineno,
            "names": names,
            "calls": calls,
            "sensitive_names": sorted(set(names) & BLOCKED),
            "dynamic_import": "__import__" in names,
        }

    return report

def main():
    report = inspect_runtime()

    output = (
        Path.cwd()
        / "runtime_state/oracle/oracle_live_execution"
        / "mtr_171_rotating_capture_safety.json"
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    for name, data in report["functions"].items():
        print("[MTR171_FUNCTION]", name)
        print("[MTR171_LINE]", data["line"])
        print("[MTR171_CALLS]", ",".join(data["calls"]))
        print(
            "[MTR171_SENSITIVE]",
            ",".join(data["sensitive_names"]) or "NONE_DIRECT",
        )
        print("[MTR171_DYNAMIC_IMPORT]", data["dynamic_import"])

    print("[MTR171_REPORT]", output)
    print("[LIVE_CAPTURE] HOLD_STARTUP_ISOLATION_REQUIRED")
    print("[EXECUTION_AUTHORITY] FALSE")
    print("[SCANNER] UNMODIFIED")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

if __name__ == "__main__":
    main()
