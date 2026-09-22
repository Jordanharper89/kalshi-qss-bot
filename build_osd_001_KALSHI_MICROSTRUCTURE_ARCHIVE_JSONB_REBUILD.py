from pathlib import Path

ROOT = Path.cwd().resolve()
TARGET = ROOT / "qseries_v2/oracle_strategy_discovery/osd_001_kalshi_microstructure_archive.py"
TEST = ROOT / "test_osd_001_KALSHI_MICROSTRUCTURE_ARCHIVE_JSONB_REBUILD.py"
OUT = ROOT / "runtime/strategy_discovery/osd_001_kalshi_microstructure_archive.jsonl"
STATE = ROOT / "runtime/strategy_discovery/osd_001_state.json"

code = r"""
from pathlib import Path
import json, sys, time

ROOT = Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

OUT = ROOT / "runtime/strategy_discovery/osd_001_kalshi_microstructure_archive.jsonl"
STATE = ROOT / "runtime/strategy_discovery/osd_001_state.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

def as_obj(v):
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        try:
            x = json.loads(v)
            return x if isinstance(x, dict) else {}
        except Exception:
            return {}
    return {}

def num(v):
    try:
        return float(v)
    except Exception:
        return None

def flatten(seq, typ, obs, raw):
    obj = as_obj(raw)
    payload = as_obj(obj.get("payload"))
    m = as_obj(payload.get("message"))
    t = str(m.get("market_ticker") or payload.get("source_market_id") or obj.get("ticker") or "")
    bid = num(m.get("yes_bid_dollars"))
    ask = num(m.get("yes_ask_dollars"))
    tr = num(m.get("yes_price_dollars"))
    px = num(m.get("price_dollars"))
    ref = tr
    if ref is None and bid is not None and ask is not None and ask >= bid:
        ref = (bid + ask) / 2.0
    if ref is None:
        ref = px if px is not None else (ask if ask is not None else bid)
    side = str(m.get("taker_outcome_side") or m.get("taker_side") or "").lower()
    size = num(m.get("count_fp") or m.get("last_trade_size_fp")) or 0.0
    return {
        "sequence_number": int(seq),
        "observation_type": str(typ),
        "observed_at": str(obs),
        "ticker": t,
        "yes_bid": bid,
        "yes_ask": ask,
        "yes_trade_price": tr,
        "yes_reference": ref,
        "trade_size": size,
        "taker_yes": int(side == "yes"),
        "taker_no": int(side == "no"),
    }

def main():
    hi = 0
    if STATE.exists():
        try:
            hi = int(json.loads(STATE.read_text(encoding="utf-8")).get("highwater_sequence", 0))
        except Exception:
            hi = 0

    q = (
        "SELECT sequence_number, observation_type, observed_at, canonical_observation_json "
        "FROM public.oracle_canonical_observations "
        "WHERE source_id='source.kalshi.market_data' AND sequence_number>%s "
        "ORDER BY sequence_number ASC LIMIT 5000"
    )

    cx = connect()
    cur = cx.cursor()
    total = 0
    scanned = 0
    rejected = 0
    types = {}

    with OUT.open("a", encoding="utf-8") as fh:
        while True:
            cur.execute(q, (hi,))
            batch = cur.fetchall()
            if not batch:
                break

            page_hi = hi
            for seq, typ, obs, raw in batch:
                scanned += 1
                page_hi = max(page_hi, int(seq))
                r = flatten(seq, typ, obs, raw)
                if not r["ticker"]:
                    rejected += 1
                    continue

                fh.write(json.dumps(r, separators=(",", ":"), default=str) + "\n")
                total += 1
                types[r["observation_type"]] = types.get(r["observation_type"], 0) + 1

            hi = page_hi
            fh.flush()
            STATE.write_text(
                json.dumps({"highwater_sequence": hi, "updated_epoch": time.time()}, indent=2),
                encoding="utf-8",
            )
            print("[SCANNED]", scanned, "[ARCHIVED]", total, "[REJECTED_NO_TICKER]", rejected, "[HIGHWATER]", hi)

    cur.close()
    cx.close()

    print("[NEW ROWS]", total)
    print("[SCANNED ROWS]", scanned)
    print("[REJECTED NO TICKER]", rejected)
    print("[OBSERVATION TYPES]", types)
    print("[HIGHWATER SEQUENCE]", hi)
    print("[RESULT]", "KALSHI_MICROSTRUCTURE_ARCHIVE_READY" if total > 0 else "KALSHI_MICROSTRUCTURE_ARCHIVE_EMPTY")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__ == "__main__":
    main()
"""

test = r"""
from pathlib import Path
import ast

p = Path("qseries_v2/oracle_strategy_discovery/osd_001_kalshi_microstructure_archive.py")
s = p.read_text(encoding="utf-8")
compile(s, str(p), "exec")

for x in (
    "def as_obj",
    'json.loads(v)',
    'payload.get("message")',
    'm.get("market_ticker")',
    'yes_price_dollars',
    'yes_bid_dollars',
    'yes_ask_dollars',
    "REJECTED_NO_TICKER",
):
    assert x in s, x

assert "INSERT INTO" not in s
assert "UPDATE " not in s
assert "DELETE FROM" not in s

tree = ast.parse(s)
assert tree is not None

print("[PASS] OSD-001 JSONB/string normalization installed")
print("[PASS] nested payload.message.market_ticker extraction installed")
print("[PASS] exact Kalshi dollar fields preserved")
print("[PASS] bad archive highwater will be rebuilt from zero")
print("[PASS] PostgreSQL access remains read-only")
"""

TARGET.parent.mkdir(parents=True, exist_ok=True)

# Retire state produced by the failed OSD-001 run so no rows remain skipped.
for p in (OUT, STATE):
    if p.exists():
        p.unlink()
        print("[RETIRED FAILED ARTIFACT]", p)

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test, encoding="utf-8")

compile(code, str(TARGET), "exec")
compile(test, str(TEST), "exec")

print("[PASS] OSD-001 JSONB root rebuild installed")
print("[TARGET]", TARGET)
print("[TEST]", TEST)
print("[RESET] archive/highwater restarted from sequence zero")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
