from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json
from .oad_305_solana_launch_security_profile import build_current_solana_launch_security_profile
from .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation
from .oad_261_universal_expansion_source_single_writer_postgresql_persistence import PRODUCER,PRIORITY,canonicalize_expansion_observation
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
BATCH_ID="oad306.solana.launch-security"
@dataclass(frozen=True,slots=True)
class LaunchSecurityPersistenceResult:
    token_address:str; raw_observations:int; canonical_observations:int; already_present:int; committed_new:int; exact_readback:int; observation_ids:tuple; execution_authority:bool=False
def persist_current_solana_launch_security(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=30.0):
    root=Path(root or Path.cwd()).resolve(); x=build_current_solana_launch_security_profile(acquisition_timeout_seconds)
    raw=(
      build_independent_crypto_observation(source_id="source.onchain.solana.launch_security."+x.token_address,provider="solana_mainnet_rpc",source_class="launch_security_chain",subject=x.token_address,observation_type="solana_launch_security_chain_evidence",payload=x.chain_mint_payload),
      build_independent_crypto_observation(source_id="source.gmgn.solana.launch_security."+x.token_address,provider="gmgn",source_class="launch_security_provider_claim",subject=x.token_address,observation_type="solana_launch_security_provider_claim",payload={"security":x.gmgn_security,"creator_deployer_claims":[{"field_path":c.field_path,"value":c.value,"provider":c.provider,"oracle_verified":c.oracle_verified} for c in x.creator_deployer_claims],"provider_claim_only":True}),
    )
    canonical=tuple(canonicalize_expansion_observation(y,BATCH_ID) for y in raw); backend=_backend(root); missing=[]; existing=0
    for i,y in enumerate(canonical):
        if _query_one(backend,y.observation_id,i) is None: missing.append(y)
        else: existing+=1
    committed=0
    if missing:
        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)
        ev=tuple(await_request(str(sub.request_id),root,float(timeout_seconds))); acc=tuple(e for e in ev if getattr(e,"accepted",False) is True)
        if len(acc)!=len(missing): raise RuntimeError("launch/security single-writer commit mismatch")
        committed=len(acc)
    ids=tuple(y.observation_id for y in canonical); rows=tuple(exact_postgresql_readback(ids,root))
    if len(rows)!=2: raise RuntimeError("launch/security exact PostgreSQL readback mismatch")
    return LaunchSecurityPersistenceResult(x.token_address,2,2,existing,committed,2,ids,False)
