"""ORACLE-235E: persisted WS route and quote lineage; read-only."""
import argparse
import json
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("runtime_state/oracle/oracle_live_execution")
DB = ROOT / "ORACLE218_DISCOVERY.sqlite3"
QUOTES = ROOT / "ORACLE235D_DLMM_FILL_TRUTH.json"
REPORT = ROOT / "ORACLE235E_WS_ROUTE_LINEAGE.json"


def stamp(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).timestamp()
        except ValueError:
            pass
    return None


def discover_cache(path):
    if not path.is_file():
        return None, "CACHE_NOT_FOUND"

    with closing(sqlite3.connect(
        path.resolve().as_uri() + "?mode=ro", uri=True
    )) as c:
        for (name,) in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ):
            if not name.replace("_", "").isalnum():
                continue
            columns = {
                x[1] for x in c.execute(
                    'PRAGMA table_info("' + name + '")'
                )
            }
            required = {"address", "slot", "observed_at"}
            if required.issubset(columns):
                return name, None
    return None, "CACHE_SCHEMA_UNKNOWN"


def latest_states(cache, addresses):
    table, error = discover_cache(cache)
    if error:
        return {}, error

    result = {}
    with closing(sqlite3.connect(
        cache.resolve().as_uri() + "?mode=ro", uri=True
    )) as c:
        for address in addresses:
            rows = c.execute(
                'SELECT slot,observed_at FROM "' + table +
                '" WHERE address=? ORDER BY slot DESC LIMIT 1',
                (address,)
            ).fetchall()
            if rows:
                result[address] = {
                    "slot": rows[0][0],
                    "timestamp": stamp(rows[0][1]),
                }
    return result, None


def evaluate(route, states, now, max_age=15, max_skew=2):
    mint, pump, dlmm = route
    rows = [states.get(pump), states.get(dlmm)]

    if any(r is None for r in rows):
        return "HOLD_MISSING_WS_ACCOUNT"

    if any(
        type(r.get("slot")) is not int
        or r.get("timestamp") is None
        for r in rows
    ):
        return "HOLD_INVALID_WS_LINEAGE"

    ages = [now - r["timestamp"] for r in rows]
    if any(age < -2 or age > max_age for age in ages):
        return "HOLD_STALE_WS_ACCOUNT"

    slots = [r["slot"] for r in rows]
    if abs(slots[0] - slots[1]) > max_skew:
        return "HOLD_WS_SLOT_SKEW"

    return "PASS_POOL_ACCOUNT_FRESHNESS_ONLY"


def load_quotes(path):
    if not path.is_file():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("build") != "ORACLE235D":
        return []

    return data.get("routes", [])


def run(registry=DB, cache=None, quote_file=QUOTES,
        report=REPORT, now=None):
    now = time.time() if now is None else now

    from qseries_v2.oracle_execution.oracle_live_pricing \
        import oracle226

    cache = Path(cache or oracle226.CACHE)

    if not registry.is_file():
        raise RuntimeError("HOLD_REGISTRY_MISSING")

    with closing(sqlite3.connect(
        registry.resolve().as_uri() + "?mode=ro", uri=True
    )) as c:
        routes = c.execute(
            "SELECT mint,pump_pool,meteora_pool "
            "FROM universal_routes"
        ).fetchall()

    addresses = {
        address for _, pump, dlmm in routes
        for address in (pump, dlmm)
    }
    states, cache_error = latest_states(cache, addresses)
    prior = load_quotes(quote_file)

    evidence = []
    for mint, pump, dlmm in routes:
        matches = [
            q for q in prior
            if mint.startswith(q.get("token_prefix", ""))
            and q.get("token_prefix")
        ]
        # Token prefixes cannot authenticate pair identity.
        unique_prefix = len(matches) == 1 and sum(
            1 for item in routes
            if item[0].startswith(
                matches[0]["token_prefix"]
            )
        ) == 1

        freshness = evaluate(
            (mint, pump, dlmm), states, now
        )
        evidence.append({
            "mint_prefix": mint[:12],
            "ws_freshness": freshness,
            "quote_prefix_match": unique_prefix,
            "quote_status": (
                matches[0]["status"]
                if unique_prefix else "HOLD_NO_UNIQUE_QUOTE"
            ),
            "bin_array_lineage_verified": False,
            "hydrated_state_ws_reconciled": False,
            "exact_pricing_certified": False,
        })

    result = {
        "build": "ORACLE235E",
        "registered_routes": len(routes),
        "cached_addresses_matched": len(states),
        "cache_error": cache_error,
        "pool_fresh_count": sum(
            x["ws_freshness"] ==
            "PASS_POOL_ACCOUNT_FRESHNESS_ONLY"
            for x in evidence
        ),
        "quote_prefix_matches": sum(
            x["quote_prefix_match"] for x in evidence
        ),
        "hydrated_state_ws_reconciled": False,
        "exact_pricing_certified": False,
        "mriya_certified": False,
        "profit_certified": False,
        "signing": False,
        "broadcast": False,
        "status": "HOLD_BIN_ARRAY_AND_HYDRATION_LINEAGE",
        "routes": evidence,
    }

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print("[ORACLE235E_RESULT]", json.dumps({
        k: v for k, v in result.items() if k != "routes"
    }, sort_keys=True))
    print("[REPORT]", report)
    return result


def test():
    now = 100.0
    route = ("mint", "pump", "dlmm")
    good = {
        "pump": {"slot": 200, "timestamp": 98},
        "dlmm": {"slot": 201, "timestamp": 99},
    }

    assert evaluate(route, good, now) == (
        "PASS_POOL_ACCOUNT_FRESHNESS_ONLY"
    )
    assert evaluate(route, {}, now) == (
        "HOLD_MISSING_WS_ACCOUNT"
    )

    bad = dict(good)
    bad["dlmm"] = {"slot": 210, "timestamp": 99}
    assert evaluate(route, bad, now) == (
        "HOLD_WS_SLOT_SKEW"
    )

    bad["dlmm"] = {"slot": 201, "timestamp": 1}
    assert evaluate(route, bad, now) == (
        "HOLD_STALE_WS_ACCOUNT"
    )

    print(
        "[ORACLE235E_TEST_PASS] "
        "route_freshness=TRUE "
        "slot_skew=TRUE "
        "staleness=TRUE "
        "no_execution=TRUE"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--run", action="store_true")
    args = p.parse_args()
    if args.test:
        test()
    if args.run:
        run()