from __future__ import annotations
import json
from urllib.request import Request,urlopen
from .oad_152_bitcoin_onchain_evidence_foundation import build_bitcoin_onchain_observation,validate_bitcoin_onchain_observation,utcnow_iso
BASE="https://mempool.space/api"; PROVIDER="mempool.space"
READ_ONLY=True; PROBABILITY_ENABLED=False; EXECUTION_AUTHORITY=False
def _get_json(url,timeout_seconds):
    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Accept":"application/json"})
    with urlopen(req,timeout=timeout_seconds) as r: return json.loads(r.read().decode("utf-8"))
def acquire_bitcoin_mempool_pressure_observations(timeout_seconds=20.0):
    mempool=_get_json(BASE+"/mempool",timeout_seconds)
    fees=_get_json(BASE+"/v1/fees/recommended",timeout_seconds)
    recent=_get_json(BASE+"/mempool/recent",timeout_seconds); now=utcnow_iso()
    pressure=build_bitcoin_onchain_observation(source_id=f"bitcoin:mempool:pressure:{mempool.get('count')}:{mempool.get('vsize')}:{now}",provider=PROVIDER,provider_role="public_mempool_observer",observation_type="mempool_pressure",subject="Bitcoin mainnet mempool pressure",observed_at=now,source_url=BASE+"/mempool",payload={"count":mempool.get("count"),"vsize":mempool.get("vsize"),"total_fee":mempool.get("total_fee"),"fee_histogram":mempool.get("fee_histogram"),"recommended_fees":fees})
    activity=build_bitcoin_onchain_observation(source_id=f"bitcoin:mempool:recent:{len(recent) if isinstance(recent,list) else 0}:{now}",provider=PROVIDER,provider_role="public_mempool_observer",observation_type="recent_unconfirmed_activity",subject="Bitcoin recent unconfirmed activity",observed_at=now,source_url=BASE+"/mempool/recent",payload={"recent_transactions":tuple(recent[:10]) if isinstance(recent,list) else tuple()})
    if not validate_bitcoin_onchain_observation(pressure) or not validate_bitcoin_onchain_observation(activity): raise RuntimeError("Bitcoin mempool observation validation failed")
    return (pressure,activity)
