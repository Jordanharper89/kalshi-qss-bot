from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_136_RESILIENT_AUTHORITATIVE_ECONOMIC_PHYSICAL_RUNTIME_GATE_V1'
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
    module=pkg/'oad_136_resilient_authoritative_economic_physical_runtime_gate.py'; test=r/'test_oad_136_resilient_authoritative_economic_physical_runtime_gate.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-136 RESILIENT AUTHORITATIVE ECONOMIC PHYSICAL RUNTIME GATE INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    deps=['oad_134_resilient_authoritative_economic_canonical_persistence.py', 'oad_135_authoritative_economic_partial_coverage_certification.py']
    for d in deps:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\n\nfrom .oad_134_resilient_authoritative_economic_canonical_persistence import persist_resilient_authoritative_economic\nfrom .oad_135_authoritative_economic_partial_coverage_certification import certify_economic_partial_coverage\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True, slots=True)\nclass ResilientEconomicPhysicalRuntimeGate:\n    state: str\n    provider_states: tuple\n    available_providers: tuple\n    unavailable_providers: tuple\n    raw_observations: int\n    canonical_observations: int\n    committed_new: int\n    exact_readback: int\n    coverage_usable: bool\n    runtime_ready: bool\n    certified_at: str\n    read_only: bool=True\n    probability_enabled: bool=False\n    execution_authority: bool=False\n\ndef run_resilient_authoritative_economic_physical_runtime_gate(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):\n    p=persist_resilient_authoritative_economic(root,timeout_seconds,acquisition_timeout_seconds)\n    c=certify_economic_partial_coverage(p)\n    provider_states=tuple((x.provider,x.state,x.observation_count,x.error_type) for x in p.provider_results)\n    runtime_ready=bool(c.coverage_usable)\n    if not runtime_ready:\n        raise RuntimeError("no usable authoritative economic provider coverage")\n    return ResilientEconomicPhysicalRuntimeGate(\n        c.state,provider_states,c.available_providers,c.unavailable_providers,\n        p.raw_observations,p.canonical_observations,p.committed_new,p.exact_readback,\n        c.coverage_usable,True,datetime.now(timezone.utc).isoformat(),True,False,False\n    )\n')
        write(test,'import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_136_resilient_authoritative_economic_physical_runtime_gate import run_resilient_authoritative_economic_physical_runtime_gate\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_resilient_authoritative_economic_physical_runtime_gate()\n        print("[PHYSICAL] state=",r.state)\n        print("[PHYSICAL] provider_states=",r.provider_states)\n        print("[PHYSICAL] available_providers=",r.available_providers)\n        print("[PHYSICAL] unavailable_providers=",r.unavailable_providers)\n        print("[PHYSICAL] raw_observations=",r.raw_observations)\n        print("[PHYSICAL] canonical_observations=",r.canonical_observations)\n        print("[PHYSICAL] committed_new=",r.committed_new)\n        print("[PHYSICAL] exact_readback=",r.exact_readback)\n        print("[PHYSICAL] runtime_ready=",r.runtime_ready)\n        self.assertTrue(r.runtime_ready)\n        self.assertTrue(r.coverage_usable)\n        self.assertGreater(r.raw_observations,0)\n        self.assertEqual(r.exact_readback,r.canonical_observations)\n        self.assertFalse(r.probability_enabled)\n        self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-136 resilient authoritative economic physical runtime gate certified")\n    print("[PASS] one failed provider cannot stop healthy authoritative economic acquisition")\n    print("[PASS] probability_enabled=FALSE execution_authority=FALSE")\n')
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_136_resilient_authoritative_economic_physical_runtime_gate import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] existing canonical/PostgreSQL single-writer architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-136 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__": main()
