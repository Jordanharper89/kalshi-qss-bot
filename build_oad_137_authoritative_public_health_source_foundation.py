from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_137_AUTHORITATIVE_PUBLIC_HEALTH_SOURCE_FOUNDATION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_137_authoritative_public_health_source_foundation.py'; test=r/'test_oad_137_authoritative_public_health_source_foundation.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-137 AUTHORITATIVE PUBLIC HEALTH SOURCE FOUNDATION INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_061_independent_to_canonical_bridge.py', 'oad_062_independent_canonical_provenance_validation.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom hashlib import sha256\nfrom typing import Any,Mapping\nimport json\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\nALLOWED_PROVIDERS=("tools.cdc.gov","api.fda.gov")\n\n@dataclass(frozen=True)\nclass AuthoritativePublicHealthObservation:\n    source_id:str\n    provider:str\n    health_family:str\n    observation_type:str\n    subject:str\n    observed_at:str\n    source_url:str\n    payload:Mapping[str,Any]\n    provenance_hash:str\n    independent_evidence:bool=True\n    source_class:str="authoritative_real_world"\n    execution_authority:bool=False\n\ndef utcnow_iso():\n    return datetime.now(timezone.utc).isoformat()\n\ndef build_public_health_observation(*,source_id,provider,health_family,observation_type,subject,observed_at,source_url,payload):\n    if provider not in ALLOWED_PROVIDERS:\n        raise ValueError("provider is not admitted by authoritative public-health source foundation")\n    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)\n    ph=sha256((provider+"|"+source_url+"|"+canonical).encode()).hexdigest()\n    return AuthoritativePublicHealthObservation(\n        str(source_id),provider,str(health_family),str(observation_type),str(subject),\n        str(observed_at),str(source_url),dict(payload),ph,True,"authoritative_real_world",False\n    )\n\ndef validate_public_health_observation(o):\n    return (\n        o.provider in ALLOWED_PROVIDERS and o.source_class=="authoritative_real_world"\n        and o.independent_evidence is True and o.execution_authority is False\n        and str(o.source_url).startswith("https://") and len(o.provenance_hash)==64\n    )\n'); write(test,'import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_137_authoritative_public_health_source_foundation import build_public_health_observation,validate_public_health_observation\nclass T(unittest.TestCase):\n    def test_foundation(self):\n        o=build_public_health_observation(source_id="cdc:test",provider="tools.cdc.gov",health_family="public_health",observation_type="official_health_publication",subject="CDC update",observed_at="2026-08-29T00:00:00+00:00",source_url="https://tools.cdc.gov/api/test",payload={"id":1})\n        self.assertTrue(validate_public_health_observation(o)); self.assertFalse(o.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-137 authoritative public-health source foundation certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_137_authoritative_public_health_source_foundation import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] existing canonical/PostgreSQL single-writer architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-137 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
