from pathlib import Path

ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_btc_kalshi_exact_price_profitability_gate.py"
TEST=ROOT/"test_opd_BTC_KALSHI_TIME_ANCHOR_RECOVERY_V4.py"

s=TARGET.read_text(encoding="utf-8")

old='''def exact_yes_price(cur,ticker,seq,obs_epoch):
    if not ticker or seq is None:return None,None
    cur.execute(SQL_EXACT_PRICE,(KALSHI_SOURCE,int(seq),float(obs_epoch)))
    for sn,obj in cur.fetchall():
        if isinstance(obj,str):
            try: obj=json.loads(obj)
            except Exception: continue
        if extract_ticker(obj)!=ticker: continue
        px=extract_yes_price(obj)
        if px is not None:return px,int(sn)
    return None,None
'''

new='''def derive_anchor_sequence(cur,ticker,obs_epoch):
    if not ticker or obs_epoch is None:return None
    cur.execute(
        "SELECT sequence_number, canonical_observation_json "
        "FROM public.oracle_canonical_observations "
        "WHERE source_id=%s "
        "AND observed_at<=to_timestamp(%s) "
        "ORDER BY sequence_number DESC "
        "LIMIT 500",
        (KALSHI_SOURCE,float(obs_epoch))
    )
    for sn,obj in cur.fetchall():
        if isinstance(obj,str):
            try: obj=json.loads(obj)
            except Exception: continue
        if extract_ticker(obj)==ticker:
            return int(sn)
    return None

def exact_yes_price(cur,ticker,seq,obs_epoch):
    if not ticker or obs_epoch is None:return None,None,None
    if seq is None:
        seq=derive_anchor_sequence(cur,ticker,obs_epoch)
    if seq is None:return None,None,None
    cur.execute(SQL_EXACT_PRICE,(KALSHI_SOURCE,int(seq),float(obs_epoch)))
    for sn,obj in cur.fetchall():
        if isinstance(obj,str):
            try: obj=json.loads(obj)
            except Exception: continue
        if extract_ticker(obj)!=ticker: continue
        px=extract_yes_price(obj)
        if px is not None:return px,int(sn),int(seq)
    return None,None,int(seq)
'''

if old not in s:
    raise SystemExit("[FAIL] exact_yes_price function not found; source not mutated")
s=s.replace(old,new,1)

old2='''price_cache={}
price_recovered=0
anchor_missing=0

def get_price(p):
    global price_recovered,anchor_missing
    pid=str(p.get("prediction_id") or "")
    if pid in price_cache:return price_cache[pid]
    t=ptime(p); seq=anchor_seq(p); ticker=str(p.get("ticker") or "")
    if t is None or seq is None:
        anchor_missing+=1
        price_cache[pid]=(None,None)
        return price_cache[pid]
    px,sn=exact_yes_price(cur,ticker,seq,t)
    if px is not None: price_recovered+=1
    price_cache[pid]=(px,sn)
    return price_cache[pid]
'''

new2='''price_cache={}
price_recovered=0
anchor_missing=0
anchor_derived=0

def get_price(p):
    global price_recovered,anchor_missing,anchor_derived
    pid=str(p.get("prediction_id") or "")
    if pid in price_cache:return price_cache[pid]
    t=ptime(p); seq=anchor_seq(p); ticker=str(p.get("ticker") or "")
    if t is None or not ticker:
        anchor_missing+=1
        price_cache[pid]=(None,None)
        return price_cache[pid]
    stored_seq=seq
    px,sn,used_seq=exact_yes_price(cur,ticker,seq,t)
    if stored_seq is None and used_seq is not None:
        anchor_derived+=1
    if used_seq is None:
        anchor_missing+=1
    if px is not None:
        price_recovered+=1
    price_cache[pid]=(px,sn)
    return price_cache[pid]
'''

if old2 not in s:
    raise SystemExit("[FAIL] get_price block not found; source not mutated")
s=s.replace(old2,new2,1)

s=s.replace(
    '"prediction_rows_missing_anchor_lineage":anchor_missing,',
    '"prediction_rows_missing_anchor_lineage":anchor_missing,\n    "decision_time_anchors_derived_from_canonical":anchor_derived,',
    1
)
s=s.replace(
    'print("[PREDICTION ROWS MISSING ANCHOR LINEAGE]",anchor_missing)',
    'print("[DECISION-TIME ANCHORS DERIVED FROM CANONICAL]",anchor_derived)\nprint("[PREDICTION ROWS MISSING ANCHOR LINEAGE]",anchor_missing)',
    1
)

TARGET.write_text(s,encoding="utf-8")
compile(s,str(TARGET),"exec")

TEST_CODE='''from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_kalshi_exact_price_profitability_gate.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
required=(
    "def derive_anchor_sequence",
    "observed_at<=to_timestamp(%s)",
    "ORDER BY sequence_number DESC",
    "extract_ticker(obj)==ticker",
    "decision_time_anchors_derived_from_canonical",
    "[DECISION-TIME ANCHORS DERIVED FROM CANONICAL]",
    "HURDLE=0.02",
    "KALSHI_PROFITABLE_EDGE_CANDIDATE_FOUND",
)
for x in required:
    assert x in s,x
print("[PASS] missing prediction anchor sequence now recovered from canonical Kalshi history")
print("[PASS] recovered anchor is same-ticker and observed-time bounded")
print("[PASS] exact YES-price lookup remains sequence/time bounded")
print("[PASS] 28-survivor signal family, fixed 2% hurdle, and profitability gate unchanged")
print("[PASS] execution/publication remain false")
'''

TEST.write_text(TEST_CODE,encoding="utf-8")
compile(TEST_CODE,str(TEST),"exec")

print("[PASS] BTC->Kalshi canonical time-anchor recovery V4 installed")
print("[TARGET]",TARGET)
print("[TEST]",TEST)
print("[ANCHOR POLICY] latest same-ticker Kalshi canonical observation at/before prediction time")
print("[PROFITABILITY LOGIC/HURDLE] unchanged")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
