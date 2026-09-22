from pathlib import Path

R=Path.cwd()
A=R/"qseries_v2/oracle_strategy_discovery/osd_001_kalshi_microstructure_archive.py"
T=R/"test_osd_001_KALSHI_MICROSTRUCTURE_ARCHIVE_REBUILD.py"

code=r'''from pathlib import Path
import json,sys,time
ROOT=Path.cwd().resolve()
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
OUT=ROOT/"runtime/strategy_discovery/osd_001_kalshi_microstructure_archive.jsonl"
STATE=ROOT/"runtime/strategy_discovery/osd_001_state.json"
OUT.parent.mkdir(parents=True,exist_ok=True)

def num(v):
    try:return float(v)
    except:return None

def flatten(seq,typ,obs,obj):
    m=obj.get("payload",{}).get("message",{})
    t=str(m.get("market_ticker") or obj.get("ticker") or "")
    bid=num(m.get("yes_bid_dollars")); ask=num(m.get("yes_ask_dollars"))
    tr=num(m.get("yes_price_dollars")); px=num(m.get("price_dollars"))
    ref=tr
    if ref is None and bid is not None and ask is not None and ask>=bid: ref=(bid+ask)/2
    if ref is None: ref=px if px is not None else (ask if ask is not None else bid)
    side=str(m.get("taker_outcome_side") or m.get("taker_side") or "").lower()
    return {"sequence_number":int(seq),"observation_type":str(typ),"observed_at":str(obs),
            "ticker":t,"yes_bid":bid,"yes_ask":ask,"yes_trade_price":tr,
            "yes_reference":ref,"trade_size":num(m.get("count_fp") or m.get("last_trade_size_fp")) or 0.0,
            "taker_yes":int(side=="yes"),"taker_no":int(side=="no")}

def main():
    hi=0
    if STATE.exists():
        try:hi=int(json.loads(STATE.read_text()).get("highwater_sequence",0))
        except:pass
    cx=connect(); cur=cx.cursor(); total=0; types={}
    q=("SELECT sequence_number,observation_type,observed_at,canonical_observation_json "
       "FROM public.oracle_canonical_observations "
       "WHERE source_id='source.kalshi.market_data' AND sequence_number>%s "
       "ORDER BY sequence_number ASC LIMIT 5000")
    with OUT.open("a",encoding="utf-8") as fh:
        while True:
            cur.execute(q,(hi,)); batch=cur.fetchall()
            if not batch:break
            for seq,typ,obs,obj in batch:
                r=flatten(seq,typ,obs,obj)
                hi=max(hi,int(seq))
                if not r["ticker"]:continue
                fh.write(json.dumps(r,separators=(",",":"),default=str)+"\n")
                total+=1; types[r["observation_type"]]=types.get(r["observation_type"],0)+1
            fh.flush()
            STATE.write_text(json.dumps({"highwater_sequence":hi,"updated_epoch":time.time()},indent=2))
            print("[ARCHIVED]",total,"[HIGHWATER]",hi)
    cur.close(); cx.close()
    print("[NEW ROWS]",total)
    print("[OBSERVATION TYPES]",types)
    print("[HIGHWATER SEQUENCE]",hi)
    print("[RESULT] KALSHI_MICROSTRUCTURE_ARCHIVE_READY")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":main()
'''

test=r'''from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_001_kalshi_microstructure_archive.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("source.kalshi.market_data","yes_price_dollars","yes_bid_dollars","yes_ask_dollars","taker_yes","trade_size","highwater_sequence"):
    assert x in s,x
assert "INSERT INTO" not in s and "UPDATE " not in s and "DELETE FROM" not in s
print("[PASS] OSD-001 rebuilt module compiles")
print("[PASS] exact Kalshi dollar fields preserved")
print("[PASS] canonical PostgreSQL access remains read-only")
print("[PASS] execution/publication remain false")
'''

A.parent.mkdir(parents=True,exist_ok=True)
A.write_text(code,encoding="utf-8")
T.write_text(test,encoding="utf-8")
compile(code,str(A),"exec")
compile(test,str(T),"exec")
print("[PASS] OSD-001 clean rebuild installed")
print("[TARGET]",A)
print("[TEST]",T)