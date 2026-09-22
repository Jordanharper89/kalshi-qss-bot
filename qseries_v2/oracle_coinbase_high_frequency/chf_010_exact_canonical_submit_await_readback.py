import hashlib,inspect,json,uuid
from datetime import datetime,timezone
from pathlib import Path

import qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence as oad261
from qseries_v2.oracle_coinbase_high_frequency.chf_009_exact_oph019_signature_bridge import submit,await_request
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback

REVISION="CHF-010-REPAIR"
WRITER_ID="oracle.coinbase_high_frequency"
PRIORITY=20

def _stable(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),default=str)

def _sha(obj):
    return hashlib.sha256(_stable(obj).encode("utf-8")).hexdigest()

def _canonical_class():
    for obj in vars(oad261).values():
        if inspect.isclass(obj) and obj.__name__=="CanonicalObservation":
            return obj
    raise RuntimeError("OAD-261 does not expose CanonicalObservation class")

def build_certification_observation():
    cls=_canonical_class()
    now=datetime.now(timezone.utc)
    token=uuid.uuid4().hex
    source_id="source.crypto.hf.coinbase.certification"
    observation_type="coinbase_hf_persistence_certification"
    payload={
        "certification_token":token,
        "product_id":"BTC-USD",
        "window_seconds":5,
        "transport":"coinbase_public_websocket",
        "execution_authority":False,
    }
    provenance={
        "adapter_id":"oracle.coinbase_high_frequency",
        "source_id":source_id,
        "transport":"websocket",
        "read_only":True,
    }
    source_observation_id=f"chf.certification.{token}"
    acquisition_batch_id=f"batch.chf010.{token}"
    content_hash=_sha({
        "source_id":source_id,
        "source_observation_id":source_observation_id,
        "observation_type":observation_type,
        "observed_at":now.isoformat(),
        "payload":payload,
        "provenance":provenance,
    })
    replay_hash=_sha({
        "source_id":source_id,
        "source_observation_id":source_observation_id,
        "observation_type":observation_type,
        "content_hash":content_hash,
    })
    observation_id=_sha({
        "schema_version":"OLA-001",
        "source_id":source_id,
        "source_observation_id":source_observation_id,
        "observation_type":observation_type,
        "content_hash":content_hash,
    })
    kwargs={
        "schema_version":"OLA-001",
        "observation_id":observation_id,
        "source_id":source_id,
        "source_observation_id":source_observation_id,
        "observation_type":observation_type,
        "observed_at":now,
        "acquired_at":now,
        "acquisition_batch_id":acquisition_batch_id,
        "payload":tuple(sorted(payload.items())),
        "provenance":tuple(sorted(provenance.items())),
        "content_hash":content_hash,
        "replay_hash":replay_hash,
        "read_only":True,
        "execution_allowed":False,
    }
    sig=inspect.signature(cls)
    required_unknown=[
        k for k,param in sig.parameters.items()
        if k not in kwargs and param.default is inspect._empty
    ]
    if required_unknown:
        raise RuntimeError(f"unsupported CanonicalObservation required fields: {required_unknown}")
    accepted={k:v for k,v in kwargs.items() if k in sig.parameters}
    return cls(**accepted),token,sig

def run_physical(root=None):
    root=Path(root or Path.cwd()).resolve()
    obs,token,canonical_sig=build_certification_observation()
    submission=submit(WRITER_ID,PRIORITY,(obs,),root=root)
    request_id=getattr(submission,"request_id",None)
    if not request_id:
        raise RuntimeError(f"OPH-019 submission missing request_id: {submission!r}")
    terminal=await_request(request_id,root=root,timeout_seconds=120.0,poll_seconds=0.05)
    rb=exact_postgresql_readback((obs.observation_id,),root=root)
    if len(rb)!=1:
        raise RuntimeError(f"exact readback count={len(rb)} expected=1")
    return obs,token,submission,terminal,rb,canonical_sig
