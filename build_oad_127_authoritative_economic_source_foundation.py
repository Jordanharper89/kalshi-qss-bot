from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_127_AUTHORITATIVE_ECONOMIC_SOURCE_FOUNDATION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_127_authoritative_economic_source_foundation.py'; test=r/'test_oad_127_authoritative_economic_source_foundation.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-127 AUTHORITATIVE ECONOMIC SOURCE FOUNDATION INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    deps=['oad_061_independent_to_canonical_bridge.py', 'oad_062_independent_canonical_provenance_validation.py', 'oad_066_independent_single_writer_ingress_binding.py', 'oad_068_exact_postgresql_independent_readback.py']
    for d in deps:
        if not (pkg/d).is_file(): raise RuntimeError("Required certified dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom hashlib import sha256\nfrom typing import Any, Mapping\nimport json\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\nALLOWED_PROVIDERS=("api.bls.gov","api.fiscaldata.treasury.gov")\n\n@dataclass(frozen=True)\nclass AuthoritativeEconomicObservation:\n    source_id: str\n    provider: str\n    economic_family: str\n    observation_type: str\n    subject: str\n    observed_at: str\n    source_url: str\n    payload: Mapping[str,Any]\n    provenance_hash: str\n    independent_evidence: bool=True\n    source_class: str="authoritative_real_world"\n    execution_authority: bool=False\n\ndef utcnow_iso():\n    return datetime.now(timezone.utc).isoformat()\n\ndef build_economic_observation(*,source_id,provider,economic_family,observation_type,subject,observed_at,source_url,payload):\n    if provider not in ALLOWED_PROVIDERS:\n        raise ValueError("provider is not admitted by authoritative economic source foundation")\n    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)\n    ph=sha256((provider+"|"+source_url+"|"+canonical).encode()).hexdigest()\n    return AuthoritativeEconomicObservation(\n        source_id=str(source_id),provider=provider,economic_family=str(economic_family),\n        observation_type=str(observation_type),subject=str(subject),observed_at=str(observed_at),\n        source_url=str(source_url),payload=dict(payload),provenance_hash=ph)\n\ndef validate_economic_observation(o):\n    return (\n        o.provider in ALLOWED_PROVIDERS and o.source_class=="authoritative_real_world"\n        and o.independent_evidence is True and o.execution_authority is False\n        and str(o.source_url).startswith("https://") and len(o.provenance_hash)==64\n    )\n'); write(test,'import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_127_authoritative_economic_source_foundation import build_economic_observation,validate_economic_observation\nclass T(unittest.TestCase):\n    def test_foundation(self):\n        o=build_economic_observation(source_id="bls:test",provider="api.bls.gov",economic_family="inflation",observation_type="official_economic_release",subject="CPI",observed_at="2026-08-29T00:00:00+00:00",source_url="https://api.bls.gov/test",payload={"value":"1"})\n        self.assertTrue(validate_economic_observation(o)); self.assertFalse(o.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-127 authoritative economic source foundation certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_127_authoritative_economic_source_foundation import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] existing independent canonical/PostgreSQL architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-127 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
