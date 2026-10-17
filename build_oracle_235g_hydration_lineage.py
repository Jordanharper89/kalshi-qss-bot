"""ORACLE-235G: inspect canonical hydrated liquidity lineage."""
import argparse
import json
import os
from pathlib import Path

ROOT = Path("runtime_state/oracle/oracle_live_execution")
REPORT = ROOT / "ORACLE235G_HYDRATION_LINEAGE.json"

def describe(value):
    result = {"type": type(value).__name__}

    if isinstance(value, dict):
        result["keys"] = sorted(str(k) for k in value)[:60]
        for key, item in list(value.items())[:60]:
            result.setdefault("field_types", {})[str(key)] = (
                type(item).__name__
            )

    elif isinstance(value, (list, tuple)):
        result["length"] = len(value)
        result["element_types"] = sorted({
            type(x).__name__ for x in value[:10]
        })

    elif hasattr(value, "__dict__"):
        fields = vars(value)
        result["keys"] = sorted(
            str(k) for k in fields
        )[:60]
        result["field_types"] = {
            str(k): type(v).__name__
            for k, v in list(fields.items())[:60]
        }

    return result

def test():
    sample = {"bin_arrays": [b"abc"], "active_id": 12}
    result = describe(sample)
    assert result["field_types"]["bin_arrays"] == "list"
    assert result["field_types"]["active_id"] == "int"
    assert describe([1, 2])["length"] == 2
    print("[ORACLE235G_TEST_PASS] structural_inspection=TRUE")

def run():
    if os.getenv("QSB_LIVE_ARM", "NO").upper() != "NO":
        raise RuntimeError("HOLD_ARMED_ENVIRONMENT")
    if os.getenv("QSB_SOLANA_PRIVATE_KEY"):
        raise RuntimeError("HOLD_PRIVATE_KEY_PRESENT")
    if not os.getenv("SOLANA_RPC_URL", "").startswith("https://"):
        raise RuntimeError("HOLD_RPC_MISSING")

    from qseries_v2.oracle_execution.solana_atomic_executor \
        import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import oracle186_direct_route_truth as d

    original_rpc = r.q87.c.rpc

    output = {
        "build": "ORACLE235G",
        "mode": "READ_ONLY",
        "signing": False,
        "broadcast": False,
        "hydration_reconciled": False,
        "pricing_certified": False,
        "mriya_certified": False,
        "pairs": [],
        "failures": []
    }

    try:
        r.q87.c.rpc = d.restricted_rpc_factory(original_rpc)
        state, _ = r.q25.prepare_once(Path.cwd())
        r.q25.bind_cached_state(state)
        r.install_proven_hot_math(state)

        for pair in list(state.get("pairs") or [])[:30]:
            row = {
                "token": str(pair.token),
                "pump_pool": str(pair.pump_pool),
                "meteora_pool": str(pair.meteora_pool),
                "token_x": str(pair.token_x),
                "token_y": str(pair.token_y),
                "decimals_x": int(pair.decimals_x),
                "decimals_y": int(pair.decimals_y)
            }

            try:
                snap = r.immutable_snapshot(pair)
                dlmm = snap.get("dlmm_state")

                row["dlmm_state"] = describe(dlmm)
                row["pump_reserves_available"] = (
                    snap.get("pump_base_reserve") is not None
                    and snap.get("pump_quote_reserve") is not None
                )

                if isinstance(dlmm, dict):
                    row["nested_structures"] = {
                        str(k): describe(v)
                        for k, v in dlmm.items()
                        if isinstance(v, (dict, list, tuple))
                    }

                row["status"] = (
                    "HYDRATED_STRUCTURE_INSPECTED"
                    if dlmm is not None
                    else "HOLD_NO_DLMM_STATE"
                )
            except Exception as exc:
                row["status"] = "HOLD_SNAPSHOT"
                row["error_type"] = type(exc).__name__

            output["pairs"].append(row)

    except Exception as exc:
        output["failures"].append(
            "PREPARATION_" + type(exc).__name__
        )
    finally:
        r.q87.c.rpc = original_rpc
        ROOT.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            json.dumps(output, indent=2),
            encoding="utf-8"
        )

    print("[ORACLE235G_RESULT]", json.dumps({
        "pairs": len(output["pairs"]),
        "failures": output["failures"],
        "hydration_reconciled": False,
        "pricing_certified": False,
        "signing": False,
        "broadcast": False
    }, sort_keys=True))

    for row in output["pairs"]:
        print("[ORACLE235G_PAIR]", json.dumps(
            {
                "token": row["token"][:12],
                "status": row["status"],
                "dlmm_state": row.get("dlmm_state"),
                "nested_structures": row.get("nested_structures")
            },
            sort_keys=True
        ))

    print("[REPORT]", REPORT)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--run", action="store_true")
    args = p.parse_args()

    if args.test:
        test()
    if args.run:
        run()