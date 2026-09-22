from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_edge_discovery"
MODULE = PKG / "oed_003_kalshi_market_family_physical_inventory.py"
TEST = ROOT / "test_oed_003_kalshi_market_family_physical_inventory.py"

assert (PKG / "oed_002_postgresql_observation_surface_inventory.py").exists()

module = r"""
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

def _dt(v):
    if isinstance(v, datetime):
        return v.astimezone(timezone.utc)
    d = datetime.fromisoformat(str(v).replace("Z","+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

def _message(obj):
    if not isinstance(obj, dict):
        return None
    p = obj.get("payload")
    if not isinstance(p, dict):
        return None
    m = p.get("message")
    return m if isinstance(m, dict) else None

def _ticker(obj):
    m = _message(obj)
    if not m:
        return None
    t = m.get("market_ticker") or obj.get("payload",{}).get("source_market_id")
    t = str(t or "")
    return t if t.startswith("KX") else None

def _family(ticker):
    return ticker.split("-",1)[0]

def inventory(root=None, max_rows=500000):
    root = Path(root or Path.cwd())
    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")
            q.execute(
                "SELECT sequence_number, observed_at, observation_type, canonical_observation_json "
                "FROM public.oracle_canonical_observations "
                "WHERE source_id='source.kalshi.market_data' "
                "ORDER BY sequence_number DESC LIMIT %s",
                (int(max_rows),)
            )
            rows = q.fetchall() or []
        c.rollback()

    families = defaultdict(lambda: {
        "rows": 0, "contracts": set(), "types": Counter(),
        "first_at": None, "last_at": None
    })

    parsed = 0
    for seq, observed_at, obs_type, obj in rows:
        ticker = _ticker(obj)
        if not ticker:
            continue
        parsed += 1
        fam = _family(ticker)
        d = families[fam]
        d["rows"] += 1
        d["contracts"].add(ticker)
        d["types"][str(obs_type)] += 1
        ts = _dt(observed_at)
        if d["first_at"] is None or ts < d["first_at"]:
            d["first_at"] = ts
        if d["last_at"] is None or ts > d["last_at"]:
            d["last_at"] = ts

    result = []
    for fam, d in families.items():
        span = (d["last_at"] - d["first_at"]).total_seconds() if d["first_at"] else 0.0
        result.append({
            "family": fam,
            "rows": d["rows"],
            "contracts": len(d["contracts"]),
            "types": dict(d["types"]),
            "first_at": d["first_at"],
            "last_at": d["last_at"],
            "span_seconds": span,
            "rows_per_contract": d["rows"] / max(1, len(d["contracts"])),
        })

    result.sort(key=lambda x: (x["rows"], x["contracts"], x["span_seconds"]), reverse=True)
    return {"schema_version":"OED-003","scanned_rows":len(rows),"parsed_rows":parsed,"families":result}
"""
MODULE.write_text(module, encoding="utf-8")

test = r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_003_kalshi_market_family_physical_inventory import inventory

s = inventory(Path.cwd())
assert s["scanned_rows"] > 0
assert s["parsed_rows"] > 0
assert s["families"]
assert all(x["family"].startswith("KX") for x in s["families"])
print("[SCANNED_ROWS]", s["scanned_rows"])
print("[PARSED_KALSHI_ROWS]", s["parsed_rows"])
print("[FAMILIES]", len(s["families"]))
print("[TOP_FAMILIES]")
for row in s["families"][:40]:
    print(" ", row)
print("[PASS] families derived from physical Kalshi tickers")
print("[PASS] no market-family list was predeclared")
print("[PASS] OED-003 Kalshi market-family physical inventory certified")
"""
TEST.write_text(test, encoding="utf-8")
py_compile.compile(str(MODULE), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OED-003 installer complete")
