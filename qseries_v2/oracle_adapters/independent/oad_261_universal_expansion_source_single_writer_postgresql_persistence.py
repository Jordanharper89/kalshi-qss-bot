from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
from .oad_253_coinbase_exchange_liquidity_orderbook_intelligence import acquire_coinbase_orderbook
from .oad_254_solana_dex_liquidity_intelligence import acquire_solana_dex_liquidity
from .oad_255_solana_stablecoin_supply_intelligence import acquire_solana_stablecoin_supply
from .oad_260_derivatives_open_interest_funding_physical_resilient_certification import acquire_resilient_derivatives_state
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
PRODUCER="oracle.crypto_independent_expansion"; PRIORITY=20
def _dt(v):
    if isinstance(v,datetime): return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    d=datetime.fromisoformat(str(v).replace("Z","+00:00")); return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
def canonicalize_expansion_observation(x,acquisition_batch_id):
    raw=RawSourceObservation.create(source_observation_id=f"{x.source_id}:{x.provenance_hash}",observed_at=_dt(x.observed_at),observation_type=x.observation_type,payload={"source_class":x.source_class,"independent_evidence":True,"provider":x.provider,"subject":x.subject,"provenance_hash":x.provenance_hash,"observation_payload":dict(x.payload)},provenance={"provider":x.provider,"source_class":x.source_class,"independent_evidence":True,"read_only":True})
    return CanonicalObservation.create(source_id=x.source_id,raw_observation=raw,acquired_at=datetime.now(timezone.utc),acquisition_batch_id=str(acquisition_batch_id))
def acquire_live_expansion_observations(timeout_seconds=20.0):
    derivatives,_,_=acquire_resilient_derivatives_state("BTCUSDT",timeout_seconds)
    return (acquire_coinbase_orderbook("BTC-USD",2,timeout_seconds),acquire_solana_dex_liquidity("SOL/USDC",25,timeout_seconds),acquire_solana_stablecoin_supply("USDC",timeout_seconds),derivatives)
@dataclass(frozen=True,slots=True)
class ExpansionPersistenceResult:
    raw_observations:int; canonical_observations:int; already_present:int; committed_new:int; exact_readback:int; providers:tuple; source_ids:tuple; observation_ids:tuple; rows:tuple; execution_authority:bool=False
def persist_live_expansion_sources(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):
    root=Path(root or Path.cwd()).resolve(); raw=tuple(acquire_live_expansion_observations(acquisition_timeout_seconds)); canonical=tuple(canonicalize_expansion_observation(x,"oad261.crypto-independent-expansion") for x in raw)
    backend=_backend(root); existing=0; missing=[]
    for i,x in enumerate(canonical):
        if _query_one(backend,x.observation_id,i) is None: missing.append(x)
        else: existing+=1
    committed=0
    if missing:
        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root); events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds))); accepted=tuple(x for x in events if getattr(x,"accepted",False) is True)
        if len(accepted)!=len(missing): raise RuntimeError("expansion-source universal single-writer commit mismatch")
        committed=len(accepted)
    ids=tuple(x.observation_id for x in canonical); rows=tuple(exact_postgresql_readback(ids,root)) if ids else ()
    if len(rows)!=len(ids): raise RuntimeError("expansion-source exact PostgreSQL readback mismatch")
    return ExpansionPersistenceResult(len(raw),len(canonical),existing,committed,len(rows),tuple(x.provider for x in raw),tuple(x.source_id for x in raw),ids,rows,False)
