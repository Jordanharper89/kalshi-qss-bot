from pathlib import Path
from collections import Counter
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import canonical_point

root=Path.cwd()
with connect(root,autocommit=False) as c:
    with c.cursor() as q:
        q.execute("SET TRANSACTION READ ONLY")
        q.execute("SET LOCAL statement_timeout='10000ms'")
        q.execute("SELECT COALESCE(MAX(sequence_number),0) FROM public.oracle_canonical_observations")
        hi=int((q.fetchone() or (0,))[0] or 0)
        lo=max(0,hi-100000)
        q.execute("""SELECT sequence_number,observed_at,source_id,observation_type,
                    canonical_observation_json
                    FROM public.oracle_canonical_observations
                    WHERE sequence_number>%s AND sequence_number<=%s
                    ORDER BY sequence_number ASC""",(lo,hi))
        rows=q.fetchall() or []
    c.rollback()

counts=Counter()
assets=Counter()
samples={}
for seq,observed,source,typ,obj in rows:
    source=str(source); typ=str(typ)
    if source=="source.kalshi.market_data":
        p=canonical_point(obj,observed.timestamp())
        if p and any(x in p["ticker"].upper() for x in ("BTC","ETH","SOL")):
            counts["kalshi_crypto"]+=1
            samples.setdefault("kalshi",p)
    elif source=="source.crypto.hf.coinbase.historical_window":
        counts["coinbase_hf"]+=1
        try:p=obj["payload"]["observation_payload"]
        except Exception:p={}
        if p.get("product_id"): assets[str(p["product_id"]).split("-")[0].upper()]+=1
        samples.setdefault("coinbase",p)
    elif source.startswith("source.crypto.condition.") and typ=="crypto_condition_snapshot":
        counts["crypto_condition"]+=1
        try:p=obj["raw_observation"]["payload"]
        except Exception:
            try:p=obj["payload"]
            except Exception:p={}
        if p.get("asset"): assets[str(p["asset"]).upper()]+=1
        samples.setdefault("condition",p)
    elif source.startswith("source.crypto.learned_case.") and typ=="crypto_verified_learned_case":
        counts["learned_case"]+=1
        try:p=obj["raw_observation"]["payload"]
        except Exception:
            try:p=obj["payload"]
            except Exception:p={}
        if p.get("asset"): assets[str(p["asset"]).upper()]+=1
        samples.setdefault("learned",p)

print("[SEQUENCE_WINDOW]",lo,hi,"[ROWS]",len(rows))
print("[COUNTS]",dict(counts))
print("[ASSETS]",dict(assets))
for k,v in samples.items():
    print("[SAMPLE_KEYS]",k,sorted(v.keys()))
assert counts["kalshi_crypto"]>0,"NO_RECENT_KALSHI_CRYPTO"
assert counts["coinbase_hf"]>0,"NO_RECENT_COINBASE_HF"
assert counts["crypto_condition"]>0,"NO_RECENT_CRYPTO_CONDITION"
assert counts["learned_case"]>0,"NO_RECENT_LEARNED_CASE"
print("[EXECUTION_AUTHORITY] FALSE")
print("[PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE")
print("[PASS] OPD-060 physical live state-at-T source census certified")
