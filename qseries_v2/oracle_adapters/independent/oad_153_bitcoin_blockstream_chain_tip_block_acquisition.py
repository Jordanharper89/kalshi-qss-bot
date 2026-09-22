from __future__ import annotations
import json
from urllib.request import Request,urlopen
from .oad_152_bitcoin_onchain_evidence_foundation import build_bitcoin_onchain_observation,validate_bitcoin_onchain_observation,utcnow_iso
BASE="https://blockstream.info/api"; PROVIDER="blockstream.info"
READ_ONLY=True; PROBABILITY_ENABLED=False; EXECUTION_AUTHORITY=False
def _get_text(url,timeout_seconds):
    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Accept":"text/plain,application/json"})
    with urlopen(req,timeout=timeout_seconds) as r: return r.read().decode("utf-8").strip()
def _get_json(url,timeout_seconds): return json.loads(_get_text(url,timeout_seconds))
def acquire_bitcoin_blockstream_chain_observations(timeout_seconds=20.0):
    height=int(_get_text(BASE+"/blocks/tip/height",timeout_seconds))
    tip_hash=_get_text(BASE+"/blocks/tip/hash",timeout_seconds)
    block=_get_json(BASE+"/block/"+tip_hash,timeout_seconds); now=utcnow_iso()
    tip=build_bitcoin_onchain_observation(source_id=f"bitcoin:blockstream:tip:{height}:{tip_hash}",provider=PROVIDER,provider_role="public_chain_observer",observation_type="chain_tip",subject="Bitcoin mainnet chain tip",observed_at=now,source_url=BASE+"/blocks/tip/height",payload={"height":height,"tip_hash":tip_hash})
    blk=build_bitcoin_onchain_observation(source_id=f"bitcoin:blockstream:block:{height}:{tip_hash}",provider=PROVIDER,provider_role="public_chain_observer",observation_type="tip_block_activity",subject=f"Bitcoin mainnet block {height}",observed_at=now,source_url=BASE+"/block/"+tip_hash,payload={"height":block.get("height"),"block_hash":block.get("id") or tip_hash,"timestamp":block.get("timestamp"),"tx_count":block.get("tx_count"),"size":block.get("size"),"weight":block.get("weight"),"merkle_root":block.get("merkle_root"),"previousblockhash":block.get("previousblockhash"),"difficulty":block.get("difficulty")})
    if not validate_bitcoin_onchain_observation(tip) or not validate_bitcoin_onchain_observation(blk): raise RuntimeError("Bitcoin Blockstream observation validation failed")
    return (tip,blk)
