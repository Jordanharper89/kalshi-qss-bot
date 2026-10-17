"""ORACLE211: Offline source inspection of exact quote dependencies."""
import argparse
import ast
import hashlib
import inspect
import json
import textwrap
from pathlib import Path

OUT = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE211_QUOTE_DEPENDENCIES.json"
)


def source_of(fn):
    source = textwrap.dedent(inspect.getsource(fn))
    ast.parse(source)
    return source


def windows(source, terms, before=9, after=5):
    lines = source.splitlines()
    selected = set()

    for index, line in enumerate(lines):
        if any(term in line for term in terms):
            lo = max(0, index - before)
            hi = min(len(lines), index + after + 1)
            selected.update(range(lo, hi))

    return [
        {"line": index + 1, "source": lines[index]}
        for index in sorted(selected)
    ]


def describe(fn, terms, full=False):
    source = source_of(fn)
    return {
        "function": fn.__module__ + "." + fn.__name__,
        "file": Path(inspect.getfile(fn)).name,
        "sha256": hashlib.sha256(source.encode()).hexdigest(),
        "source_lines": len(source.splitlines()),
        "source": (
            [
                {"line": index, "source": line}
                for index, line in enumerate(
                    source.splitlines(), 1
                )
            ]
            if full else windows(source, terms)
        ),
    }


def test():
    def fixture(amount):
        net = amount - 10
        if net <= 0:
            raise RuntimeError("TOKEN_NET_ZERO")
        return net

    result = describe(fixture, ["TOKEN_NET_ZERO"])
    assert result["source"]
    assert any(
        "TOKEN_NET_ZERO" in x["source"]
        for x in result["source"]
    )
    print("[ORACLE211_TEST_PASS] source_windows=TRUE")


def run():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze,
        runtime as r,
    )

    freeze.freeze()

    quote = r.q18.exact_snapshot_opportunities
    scope = quote.__globals__

    components = {
        "exact_quote": describe(
            quote,
            [
                "REVERSE_TOKEN_NET_ZERO",
                "FORWARD_TOKEN_NET_ZERO",
                "dlmm_quote_snapshot",
                "worker().buy",
                "worker().sell",
                "token_net(",
            ],
        ),
    }

    token_net_fn = scope.get("token_net")
    if callable(token_net_fn):
        components["token_net"] = describe(
            token_net_fn, ["return", "raise"], full=True
        )

    core = scope.get("core")
    dlmm = getattr(core, "dlmm_quote_snapshot", None)
    if callable(dlmm):
        components["meteora_quote"] = describe(
            dlmm, ["return", "raise", "amount", "bin", "liquid"],
            full=True
        )

    immutable = getattr(r, "immutable_snapshot", None)
    if callable(immutable):
        components["snapshot"] = describe(
            immutable,
            ["return", "raise", "pool", "array", "snapshot"],
        )

    report = {
        "build": "ORACLE211",
        "status": "OFFLINE_SOURCE_ONLY",
        "components": components,
        "diagnosis_confirmed": False,
        "rpc_requested": False,
        "signing": False,
        "broadcast": False,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    for name, component in components.items():
        print(
            "========== %s | %s =========="
            % (name.upper(), component["file"])
        )
        for line in component["source"]:
            print(
                "%04d %s"
                % (line["line"], line["source"])
            )

    print("[ORACLE211_REPORT]", OUT)
    freeze.freeze()
    print(
        "[ORACLE211_PASS] executor_unchanged=TRUE "
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