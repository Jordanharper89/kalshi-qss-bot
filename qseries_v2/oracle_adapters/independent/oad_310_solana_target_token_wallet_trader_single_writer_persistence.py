from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json

from .oad_309_solana_target_token_wallet_trader_coverage_acquisition import acquire_target_token_wallet_trader_coverage
from .oad_261_universal_expansion_source_single_writer_postgresql_persistence import PRODUCER,PRIORITY,canonicalize_expansion_observation
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
BATCH_ID="oad310.gmgn.target-token.wallet-trader"

@dataclass(frozen=True,slots=True)
class Raw:
    source_id:str
    provenance_hash:str
    observed_at:object
    observation_type:str
    source_class:str
    provider:str
    subject:str
    payload:dict
    execution_authority:bool=False

@dataclass(frozen=True,slots=True)
class TargetTokenWalletTraderPersistenceResult:
    token_address:str
    acquisition_state:str
    raw_observations:int
    canonical_observations:int
    already_present:int
    committed_new:int
    exact_readback:int
    observation_ids:tuple
    retry_after_seconds:float|None
    persistence_state:str
    execution_authority:bool=False

def _h(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def persist_target_token_wallet_trader_coverage(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=30.0):
    root=Path(root or Path.cwd()).resolve()
    x=acquire_target_token_wallet_trader_coverage(root=root,timeout_seconds=acquisition_timeout_seconds)

    # A provider-wide rate-limit HOLD is not evidence and must never be persisted.
    if x.state=="RATE_LIMITED_HOLD":
        return TargetTokenWalletTraderPersistenceResult(
            x.token_address,x.state,0,0,0,0,0,(),
            x.retry_after_seconds,"RATE_LIMITED_HOLD_NO_WRITE",False
        )
    if x.state!="ACQUIRED":
        raise RuntimeError("unsupported target-token acquisition state: "+str(x.state))

    now=datetime.now(timezone.utc)
    sections={
        "holders":{
            "token_address":x.token_address,
            "row_count":x.holder_rows,
            "claims":[c.claim_payload for c in x.provider_claims if c.claim_kind=="holder"],
            "provider_claim_only":True,
        },
        "traders":{
            "token_address":x.token_address,
            "row_count":x.trader_rows,
            "claims":[c.claim_payload for c in x.provider_claims if c.claim_kind=="trader"],
            "provider_claim_only":True,
        },
    }
    raw=[]
    for kind,payload in sections.items():
        sid=f"source.gmgn.solana.token.{x.token_address}.{kind}"
        raw.append(Raw(
            sid,
            _h({"source_id":sid,"observed_at":now,"payload":payload}),
            now,
            "gmgn_solana_"+kind,
            "wallet_trader_intelligence",
            "gmgn",
            x.token_address,
            payload,
            False,
        ))

    can=tuple(canonicalize_expansion_observation(y,BATCH_ID) for y in raw)
    backend=_backend(root); missing=[]; existing=0
    for i,y in enumerate(can):
        if _query_one(backend,y.observation_id,i) is None:
            missing.append(y)
        else:
            existing+=1

    committed=0
    if missing:
        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)
        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))
        accepted=tuple(e for e in events if getattr(e,"accepted",False) is True)
        if len(accepted)!=len(missing):
            raise RuntimeError("target-token wallet/trader single-writer commit mismatch")
        committed=len(accepted)

    ids=tuple(y.observation_id for y in can)
    rows=tuple(exact_postgresql_readback(ids,root))
    if len(rows)!=2:
        raise RuntimeError("target-token wallet/trader exact PostgreSQL readback mismatch")

    return TargetTokenWalletTraderPersistenceResult(
        x.token_address,x.state,2,2,existing,committed,2,ids,None,
        "PERSISTED_EXACT_TARGET_TOKEN_EVIDENCE",False
    )
