import hashlib,json,uuid
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback
from qseries_v2.oracle_coinbase_high_frequency.chf_009_exact_oph019_signature_bridge import submit,await_request

REVISION="CHF-010-OAD261-NATIVE-CANONICALIZATION-REBUILD"
WRITER_ID="oracle.coinbase_high_frequency"
PRIORITY=20

@dataclass(frozen=True)
class CHFExpansionObservation:
    source_id:str
    source_class:str
    provider:str
    subject:str
    provenance_hash:str
    observation_type:str
    observed_at:str
    payload:tuple

def _hash(x):
    raw=json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()
    return hashlib.sha256(raw).hexdigest()

def build_fixture():
    token=uuid.uuid4().hex
    observed_at=datetime.now(timezone.utc).isoformat()
    payload={
        "certification_token":token,
        "product_id":"BTC-USD",
        "window_seconds":5,
        "transport":"coinbase_public_websocket",
        "raw_external":True,
        "oracle_derived":False,
        "kalshi_market":False,
        "probability_enabled":False,
        "direction_enabled":False,
        "publication_allowed":False,
        "execution_authority":False,
    }
    ph=_hash({
        "provider":"coinbase",
        "source_class":"RAW_EXTERNAL",
        "subject":"BTC-USD",
        "observed_at":observed_at,
        "payload":payload,
    })
    return CHFExpansionObservation(
        "source.crypto.hf.coinbase.certification",
        "RAW_EXTERNAL",
        "coinbase",
        "BTC-USD",
        ph,
        "coinbase_hf_persistence_certification",
        observed_at,
        tuple(sorted(payload.items())),
    ),token

def run_physical(root=None):
    root=Path(root or Path.cwd()).resolve()
    expansion,token=build_fixture()
    batch_id=f"chf010.{token}"
    canonical=canonicalize_expansion_observation(expansion,batch_id)
    submission=submit(WRITER_ID,PRIORITY,(canonical,),root=root)
    request_id=getattr(submission,"request_id",None)
    if not request_id:
        raise RuntimeError(f"submission returned no request_id: {submission!r}")
    terminal=await_request(request_id,root=root,timeout_seconds=120.0,poll_seconds=0.05)
    rb=exact_postgresql_readback((canonical.observation_id,),root=root)
    if len(rb)!=1:
        raise RuntimeError(f"exact readback count={len(rb)} expected=1")
    if rb[0].observation_id!=canonical.observation_id:
        raise AssertionError("readback observation identity mismatch")
    return canonical,token,batch_id,submission,terminal,rb
