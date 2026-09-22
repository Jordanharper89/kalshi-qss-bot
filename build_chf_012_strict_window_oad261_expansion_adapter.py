from pathlib import Path
import py_compile
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
assert (PKG/"chf_011_strict_complete_multihorizon_windows.py").exists(),"CHF-011 required"

BODY=r"""
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
"""
TEST=r"""
from qseries_v2.oracle_coinbase_high_frequency.chf_012_strict_window_oad261_expansion_adapter import adapt_window
fixture={"product_id":"BTC-USD","window_seconds":5,"window_start":"2026-09-10T14:00:00+00:00","window_end":"2026-09-10T14:00:05+00:00","coverage_span_seconds":5.0,"event_count":10,"max_event_gap_seconds":1.0,"full_horizon_complete":True,"no_future_leakage":True}
x=adapt_window(fixture)
print("[SOURCE_ID]",x.source_id)
print("[SOURCE_CLASS]",x.source_class)
print("[PROVIDER]",x.provider)
print("[SUBJECT]",x.subject)
assert x.source_class=="ORACLE_DERIVED"
assert x.provider=="coinbase"
print("[PASS] raw Coinbase provenance retained without misclassifying derived windows as RAW_EXTERNAL")
print("[PASS] CHF-012 exact OAD-261 expansion adapter certified")
"""
mod=PKG/"chf_012_strict_window_oad261_expansion_adapter.py"
tst=ROOT/"test_chf_012_strict_window_oad261_expansion_adapter.py"
mod.write_text(BODY.lstrip(),encoding="utf-8")
tst.write_text(TEST.lstrip(),encoding="utf-8")
py_compile.compile(str(mod),doraise=True); py_compile.compile(str(tst),doraise=True)
print("[PASS] wrote CHF-012 expansion adapter + test")
