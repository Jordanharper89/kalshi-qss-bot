from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_130_AUTHORITATIVE_ECONOMIC_CANONICAL_PERSISTENCE_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_130_authoritative_economic_canonical_persistence.py'; test=r/'test_oad_130_authoritative_economic_canonical_persistence.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-130 AUTHORITATIVE ECONOMIC CANONICAL PERSISTENCE INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    deps=['oad_061_independent_to_canonical_bridge.py', 'oad_062_independent_canonical_provenance_validation.py', 'oad_066_independent_single_writer_ingress_binding.py', 'oad_068_exact_postgresql_independent_readback.py', 'oad_128_official_bls_economic_adapter.py', 'oad_129_official_treasury_fiscal_data_adapter.py']
    for d in deps:
        if not (pkg/d).is_file(): raise RuntimeError("Required certified dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_061_independent_to_canonical_bridge import canonicalize_independent_observation\nfrom .oad_062_independent_canonical_provenance_validation import validate_independent_canonical\nfrom .oad_066_independent_single_writer_ingress_binding import submit_independent_canonical_batch,await_independent_commit\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom .oad_128_official_bls_economic_adapter import acquire_bls_latest_economic_observations\nfrom .oad_129_official_treasury_fiscal_data_adapter import acquire_treasury_debt_observation\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass AuthoritativeEconomicPersistence:\n    raw_observations:int\n    canonical_observations:int\n    provenance_validated:int\n    already_present:int\n    committed_new:int\n    exact_readback:int\n    providers:tuple\n    observation_ids:tuple\n    rows:tuple\n    execution_authority:bool=False\n\ndef persist_current_authoritative_economic(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):\n    raw=tuple(acquire_bls_latest_economic_observations(acquisition_timeout_seconds))+tuple(acquire_treasury_debt_observation(acquisition_timeout_seconds))\n    canonical=tuple(canonicalize_independent_observation(x,"oad130.authoritative-economic") for x in raw)\n    validations=tuple(validate_independent_canonical(x) for x in canonical)\n    if not all(v.valid for v in validations): raise RuntimeError("authoritative economic canonical provenance failed")\n    backend=_backend(root)\n    existing=[]; missing=[]\n    for i,x in enumerate(canonical):\n        row=_query_one(backend,x.observation_id,i)\n        (missing if row is None else existing).append(x if row is None else row)\n    committed=0\n    if missing:\n        sub=submit_independent_canonical_batch(tuple(missing),root)\n        ev=tuple(await_independent_commit(str(sub.request_id),root,timeout_seconds))\n        accepted=tuple(x for x in ev if getattr(x,"accepted",False) is True)\n        if len(accepted)!=len(missing): raise RuntimeError("economic single-writer commit count mismatch")\n        committed=len(accepted)\n    ids=tuple(x.observation_id for x in canonical)\n    rows=tuple(exact_postgresql_readback(ids,root)) if ids else tuple()\n    if len(rows)!=len(ids): raise RuntimeError("economic exact PostgreSQL readback mismatch")\n    return AuthoritativeEconomicPersistence(\n        len(raw),len(canonical),len(validations),len(existing),committed,len(rows),\n        tuple(sorted({x.provider for x in raw})),ids,rows,False)\n'); write(test,'import unittest\nfrom unittest.mock import patch\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent import oad_130_authoritative_economic_canonical_persistence as m\nfrom qseries_v2.oracle_adapters.independent.oad_127_authoritative_economic_source_foundation import build_economic_observation\nclass T(unittest.TestCase):\n    def test_existing_architecture_reuse(self):\n        o=build_economic_observation(source_id="bls:test:1",provider="api.bls.gov",economic_family="inflation",observation_type="official_economic_release",subject="CPI",observed_at="2026-08-29T00:00:00+00:00",source_url="https://api.bls.gov/test",payload={"value":"1"})\n        c=m.canonicalize_independent_observation(o,"test")\n        with patch.object(m,"acquire_bls_latest_economic_observations",return_value=(o,)),patch.object(m,"acquire_treasury_debt_observation",return_value=()),patch.object(m,"_backend",return_value=object()),patch.object(m,"_query_one",return_value=SimpleNamespace(observation_id=c.observation_id)),patch.object(m,"exact_postgresql_readback",return_value=(SimpleNamespace(observation_id=c.observation_id),)):\n            r=m.persist_current_authoritative_economic()\n        print("[RAW]",r.raw_observations); print("[EXACT_READBACK]",r.exact_readback)\n        self.assertEqual(r.raw_observations,1); self.assertEqual(r.exact_readback,1); self.assertEqual(r.committed_new,0)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-130 authoritative economic canonical/persistence contract certified")\n    print("[PASS] existing OAD-061/OAD-062/OAD-066/OAD-068 architecture reused")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_130_authoritative_economic_canonical_persistence import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] existing independent canonical/PostgreSQL architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-130 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
