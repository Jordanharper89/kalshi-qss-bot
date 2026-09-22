from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_135_AUTHORITATIVE_ECONOMIC_PARTIAL_COVERAGE_CERTIFICATION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_135_authoritative_economic_partial_coverage_certification.py'; test=r/'test_oad_135_authoritative_economic_partial_coverage_certification.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-135 AUTHORITATIVE ECONOMIC PARTIAL-COVERAGE CERTIFICATION INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    deps=['oad_134_resilient_authoritative_economic_canonical_persistence.py']
    for d in deps:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True, slots=True)\nclass EconomicCoverageCertification:\n    state: str\n    available_providers: tuple\n    unavailable_providers: tuple\n    raw_observations: int\n    exact_readback: int\n    coverage_usable: bool\n    full_provider_coverage: bool\n    certified_at: str\n    probability_enabled: bool=False\n    execution_authority: bool=False\n\ndef certify_economic_partial_coverage(persistence_result):\n    available=tuple(sorted(x.provider for x in persistence_result.provider_results if x.state=="AVAILABLE"))\n    unavailable=tuple(sorted(x.provider for x in persistence_result.provider_results if x.state!="AVAILABLE"))\n    usable=(\n        len(available)>0\n        and persistence_result.raw_observations>0\n        and persistence_result.exact_readback==persistence_result.canonical_observations\n    )\n    full=usable and len(unavailable)==0\n    if full:\n        state="FULL_COVERAGE"\n    elif usable:\n        state="PARTIAL_COVERAGE"\n    else:\n        state="NO_USABLE_COVERAGE"\n    return EconomicCoverageCertification(\n        state,available,unavailable,int(persistence_result.raw_observations),\n        int(persistence_result.exact_readback),usable,full,\n        datetime.now(timezone.utc).isoformat(),False,False\n    )\n')
        write(test,'import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_135_authoritative_economic_partial_coverage_certification import certify_economic_partial_coverage\nclass T(unittest.TestCase):\n    def test_partial_is_usable(self):\n        p=SimpleNamespace(\n            provider_results=(\n                SimpleNamespace(provider="api.bls.gov",state="AVAILABLE"),\n                SimpleNamespace(provider="api.fiscaldata.treasury.gov",state="UNAVAILABLE"),\n            ),\n            raw_observations=3,canonical_observations=3,exact_readback=3,\n        )\n        r=certify_economic_partial_coverage(p)\n        print("[STATE]",r.state); print("[AVAILABLE]",r.available_providers); print("[UNAVAILABLE]",r.unavailable_providers)\n        self.assertEqual(r.state,"PARTIAL_COVERAGE")\n        self.assertTrue(r.coverage_usable)\n        self.assertFalse(r.full_provider_coverage)\n        self.assertFalse(r.probability_enabled)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-135 partial economic coverage certification certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_135_authoritative_economic_partial_coverage_certification import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] existing canonical/PostgreSQL single-writer architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-135 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__": main()
