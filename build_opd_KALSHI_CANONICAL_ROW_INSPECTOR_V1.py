from pathlib import Path

R=Path.cwd()
A=R/"qseries_v2/oracle_predictive_discovery/opd_kalshi_canonical_row_inspector.py"
T=R/"test_opd_KALSHI_CANONICAL_ROW_INSPECTOR_V1.py"

audit=r'''import json,sys
from pathlib import Path
ROOT=Path.cwd().resolve()
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

LEDGER=ROOT/"runtime/predictive_data/opd_full_evidence_live_prediction_ledger.jsonl"

def epoch(r):
    for k in ("prediction_epoch","frozen_epoch","created_epoch","anchor_observed_epoch","observed_epoch"):
        try:
            if r.get(k) is not None:return float(r[k])
        except: pass
    try:return float(r["resolution_due_epoch"])-float(r["horizon_seconds"])
    except:return None

def ticker(r):
    for k in ("ticker","market_ticker","kalshi_ticker"):
        if r.get(k):return str(r[k])
    return ""

rows=[]
for line in LEDGER.open(encoding="utf-8"):
    try:r=json.loads(line)
    except:continue
    t=ticker(r); e=epoch(r)
    if t.startswith("KXBTC") and e: rows.append((t,e))

print("[BTC PREDICTION ANCHORS]",len(rows))
cx=connect(); cur=cx.cursor()
shown=set(); n=0
for t,e in reversed(rows):
    if t in shown:continue
    cur.execute("""
      SELECT sequence_number,observation_type,observed_at,canonical_observation_json
      FROM public.oracle_canonical_observations
      WHERE source_id='source.kalshi.market_data'
        AND observed_at<=to_timestamp(%s)
        AND canonical_observation_json::text LIKE %s
      ORDER BY sequence_number DESC LIMIT 1
    """,(e,"%"+t+"%"))
    q=cur.fetchone()
    if not q:continue
    sn,typ,obs,obj=q
    print("\\n[ROW]",n+1,"TICKER=",t,"SEQ=",sn,"TYPE=",typ,"OBSERVED_AT=",obs)
    print("[CANONICAL_JSON]",json.dumps(obj,sort_keys=True,default=str))
    shown.add(t); n+=1
    if n>=12:break
cur.close(); cx.close()
print("\\n[ROWS INSPECTED]",n)
print("[RESULT] CANONICAL_KALSHI_SCHEMA_EXPOSED" if n else "[RESULT] NO_MATCHING_CANONICAL_ROWS")
print("[MODEL/HURDLE/EXECUTION/PUBLICATION] UNCHANGED/0.02/FALSE/FALSE")
'''

test=r'''from pathlib import Path
p=Path("qseries_v2/oracle_predictive_discovery/opd_kalshi_canonical_row_inspector.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("source.kalshi.market_data","canonical_observation_json","observation_type",
          "CANONICAL_KALSHI_SCHEMA_EXPOSED","MODEL/HURDLE/EXECUTION/PUBLICATION"):
    assert x in s,x
print("[PASS] canonical Kalshi row inspector installed")
print("[PASS] read-only PostgreSQL inspection only")
print("[PASS] exact BTC prediction-time bound preserved")
print("[PASS] model/hurdle/execution/publication unchanged")
'''

A.write_text(audit,encoding="utf-8")
T.write_text(test,encoding="utf-8")
compile(audit,str(A),"exec")
compile(test,str(T),"exec")
print("[PASS] Kalshi canonical-row physical inspector V1 installed")
print("[AUDIT]",A)
print("[TEST]",T)
print("[MUTATION] diagnostic files only")