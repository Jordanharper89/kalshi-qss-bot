from collections import Counter,defaultdict
import json
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
ROOT=Path.cwd();cases=list(read_crypto_learned_case_history(per_asset_limit=8192))
print("[LEARNED_CASES]",len(cases));print("[LEARNED_HORIZONS]",dict(Counter(int(x.horizon_seconds) for x in cases)))
for a in sorted({x.asset for x in cases}):
    rs=[x for x in cases if x.asset==a];print("[ASSET_LEARNING]",a,"n=",len(rs),"horizons=",dict(Counter(int(x.horizon_seconds) for x in rs)))
with connect(ROOT,autocommit=False) as c:
    with c.cursor() as q:
        q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='15000ms'")
        q.execute("SELECT observed_at,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations ORDER BY sequence_number DESC LIMIT 400000")
        rows=q.fetchall() or []
    c.rollback()
kal=defaultdict(list);ind=defaultdict(list)
for ts,source,typ,obj in rows:
    try:text=json.dumps(obj if isinstance(obj,dict) else json.loads(obj),separators=(",",":")).upper()
    except Exception:text=""
    asset=next((a for a in ("BTC","ETH","SOL") if a in text or a in str(source).upper()),None)
    if not asset or not ts:continue
    if str(source)=="source.kalshi.market_data":kal[asset].append(ts)
    elif any(x in str(source).lower() for x in ("crypto","coinbase","bitcoin","ethereum","solana")):ind[asset].append(ts)
for a in ("BTC","ETH","SOL"):
    kt=kal[a];it=ind[a];kspan=(max(kt)-min(kt)).total_seconds() if len(kt)>1 else 0;ispan=(max(it)-min(it)).total_seconds() if len(it)>1 else 0
    print("[PHYSICAL_DEPTH]",a,"kalshi_rows=",len(kt),"kalshi_span_s=",round(kspan,1),"independent_rows=",len(it),"independent_span_s=",round(ispan,1))
    for h in (30,60,300,900,3600):
        feasible=(kspan>=h and ispan>=h);learned=sum(1 for x in cases if x.asset==a and int(x.horizon_seconds)==h)
        print("[TARGET]",a,"horizon_s=",h,"history_feasible=",feasible,"existing_learned_cases=",learned)
print("[SETTLEMENT_TARGET] requires exact proposition/expiry/outcome lineage; not inferred from short-horizon return")
print("[PRICE_PATH_TARGETS] future return, MFE, MAE, time-to-extreme, reversal, spread/liquidity stress are distinct labels")
print("[PASS] OPA-015 multi-target predictive feasibility audit complete")
