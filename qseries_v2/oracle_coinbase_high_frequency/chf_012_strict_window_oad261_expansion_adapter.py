import hashlib,json
from dataclasses import dataclass

REVISION="CHF-012"

@dataclass(frozen=True)
class CHFWindowExpansion:
    source_id:str
    source_class:str
    provider:str
    subject:str
    provenance_hash:str
    observation_type:str
    observed_at:str
    payload:tuple

def _hash(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def adapt_window(row):
    if not row.get("full_horizon_complete"):
        raise ValueError("incomplete window cannot enter OAD-261")
    if not row.get("no_future_leakage"):
        raise ValueError("future-leaking window cannot enter OAD-261")
    product=str(row["product_id"])
    seconds=int(row["window_seconds"])
    payload=dict(row)
    payload["raw_external_provenance"]=True
    payload["derived_by"]="CHF-011"
    ph=_hash({
        "product_id":product,
        "window_seconds":seconds,
        "window_start":row["window_start"],
        "window_end":row["window_end"],
        "payload":payload,
    })
    slug=product.lower().replace("-","_")
    return CHFWindowExpansion(
        source_id=f"source.crypto.hf.coinbase.window.{slug}.{seconds}s",
        source_class="ORACLE_DERIVED",
        provider="coinbase",
        subject=product,
        provenance_hash=ph,
        observation_type="coinbase_hf_complete_condition_window",
        observed_at=row["window_end"],
        payload=tuple(sorted(payload.items())),
    )
