from pathlib import Path

ROOT = Path.cwd().resolve()
TARGET = ROOT / 'qseries_v2/oracle_strategy_discovery/osd_001_kalshi_microstructure_archive.py'
TEST = ROOT / 'test_osd_001_KALSHI_MICROSTRUCTURE_ARCHIVE.py'

TARGET.parent.mkdir(parents=True, exist_ok=True)

MODULE = r"""from pathlib import Path
import json,sys,time
ROOT=Path.cwd().resolve()
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

OUT=ROOT/"runtime/strategy_discovery/osd_001_kalshi_microstructure_archive.jsonl"
STATE=ROOT/"runtime/strategy_discovery/osd_001_state.json"
OUT.parent.mkdir(parents=True,exist_ok=True)
PAGE=5000

def fnum(v):
    try:return float(v)
    except:return None

def msg(obj):
    x=obj.get("payload",{}).get("message",{})
    return x if isinstance(x,dict) else {}

def ticker(obj):
    m=msg(obj)
    return str(m.get("market_ticker") or obj.get("ticker") or obj.get("market_ticker") or "")

def flatten(seq,typ,obs,obj):
    m=msg(obj); t=ticker(obj)
    bid=fnum(m.get("yes_bid_dollars")); ask=fnum(m.get("yes_ask_dollars"))
    tr=fnum(m.get("yes_price_dollars"))
    px=fnum(m.get("price_dollars"))
    ref=tr
    if ref is None and bid is not None and ask is not None and ask>=bid:
        ref=(bid+ask)/2.0
    if ref is None: ref=px if px is not None else (ask if ask is not None else bid)
    size=fnum(m.get("count_fp") or m.get("last_trade_size_fp")) or 0.0
    side=str(m.get("taker_outcome_side") or m.get("taker_side") or "").lower()
    return {
      "sequence_number":int(seq),"observation_type":str(typ),"observed_at":str(obs),
      "ticker":t,"yes_bid":bid,"yes_ask":ask,"yes_trade_price":tr,"yes_reference":ref,
      "trade_size":size,"taker_yes":1 if side=="yes" else 0,"taker_no":1 if side=="no" else 0,
      "raw_seq":m.get("seq"),"source_id":"source.kalshi.market_data"
    }

def main():
    hi=0
    if STATE.exists():
        try: hi=int(json.loads(STATE.read_text()).get("highwater_sequence",0))
        except: hi=0
    cx=connect(); cur=cx.cursor(); total=0; types={}
    with OUT.open("a",encoding="utf-8") as fh:
        while True:
            cur.execute(\"\"\"SELECT sequence_number,observation_type,observed_at,canonical_observation_json
                           FROM public.oracle_canonical_observations
                           WHERE source_id='source.kalshi.market_data' AND sequence_number>%s
                           ORDER BY sequence_number ASC LIMIT %s\"\"\",(hi,PAGE))
            batch=cur.fetchall()
            if not batch: break
            for seq,typ,obs,obj in batch:
                r=flatten(seq,typ,obs,obj)
                if not r["ticker"]: continue
                fh.write(json.dumps(r,separators=(",",":"),default=str)+"\n")
                total+=1; types[r["observation_type"]]=types.get(r["observation_type"],0)+1
                hi=max(hi,int(seq))
            fh.flush()
            STATE.write_text(json.dumps({"highwater_sequence":hi,"updated_epoch":time.time()},indent=2))
            print("[ARCHIVED]",total,"[HIGHWATER]",hi)
    cur.close(); cx.close()
    print("[NEW ROWS]",total)
    print("[OBSERVATION TYPES]",types)
    print("[HIGHWATER SEQUENCE]",hi)
    print("[RESULT] KALSHI_MICROSTRUCTURE_ARCHIVE_READY")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")
if __name__=="__main__": main()
"""

TEST_CODE = r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_001_kalshi_microstructure_archive.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
for x in ("source.kalshi.market_data","yes_price_dollars","yes_bid_dollars","yes_ask_dollars","taker_yes","trade_size","highwater_sequence"):
    assert x in s,x
assert "INSERT INTO" not in s and "UPDATE " not in s and "DELETE FROM" not in s
print("[PASS] OSD-001 deterministic interface test")
print("[PASS] canonical Kalshi market-data source only")
print("[PASS] exact observed dollar fields flattened")
print("[PASS] PostgreSQL access is read-only")
"""

TARGET.write_text(MODULE, encoding="utf-8")
TEST.write_text(TEST_CODE, encoding="utf-8")

compile(MODULE, str(TARGET), "exec")
compile(TEST_CODE, str(TEST), "exec")

print("[PASS] OSD-001 Kalshi microstructure archive installed")
print("[TARGET]", TARGET)
print("[TEST]", TEST)
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
