from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_189_CRYPTO_LEARNED_CASE_EXACT_HISTORY_READBACK_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import CanonicalPersistenceQueryRequest\nfrom .oad_068_exact_postgresql_independent_readback import _backend\nfrom .oad_188_crypto_verified_learned_case_postgresql_persistence import SOURCE_PREFIX\n\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; EXECUTION_AUTHORITY=False\nASSETS=("BTC","ETH","SOL")\n\n@dataclass(frozen=True,slots=True)\nclass LearnedCase:\n    observation_id:str; asset:str; experience_id:str; snapshot_at:str; condition_vector:tuple; temporal_vector:tuple\n    condition_hash:str; experience_hash:str; lineage_hash:str; horizon_seconds:int; outcome_observed_at:str\n    return_fraction:float; return_percent:float; outcome_hash:str; learning_event_hash:str; exact_interval:bool\n\ndef read_crypto_learned_case_history(root=None,assets=ASSETS,per_asset_limit=512):\n    root=Path(root or Path.cwd()).resolve(); backend=_backend(root); out=[]\n    for i,a in enumerate(tuple(assets)):\n        req=CanonicalPersistenceQueryRequest.by_source_id(query_id=f"query.oad189.{i}.{a.lower()}",backend_id=backend.backend_id,source_id=f"{SOURCE_PREFIX}{a.lower()}",limit=int(per_asset_limit),requested_at=datetime.now(timezone.utc),query_metadata={"read_only":True,"build_id":"OAD-189"})\n        for row in tuple(backend.query(request=req)):\n            if row.observation_type!="crypto_verified_learned_case": continue\n            p=dict(row.payload)\n            if not bool(p.get("exact_interval")): continue\n            out.append(LearnedCase(str(row.observation_id),str(p["asset"]),str(p["experience_id"]),str(p["snapshot_at"]),tuple(p["condition_vector"]),tuple(p["temporal_vector"]),str(p["condition_hash"]),str(p["experience_hash"]),str(p["lineage_hash"]),int(p["horizon_seconds"]),str(p["outcome_observed_at"]),float(p["return_fraction"]),float(p["return_percent"]),str(p["outcome_hash"]),str(p["learning_event_hash"]),True))\n    return tuple(sorted(out,key=lambda x:(x.asset,x.snapshot_at,x.experience_id)))\n'
TEST_SOURCE='import unittest\nfrom datetime import datetime,timezone\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_189_crypto_learned_case_exact_history_readback as m\nclass B:\n    backend_id="b"\n    def query(self,request):\n        a=request.source_id.rsplit(".",1)[-1].upper()\n        return (SimpleNamespace(observation_id="o"+a,observation_type="crypto_verified_learned_case",payload=tuple({"asset":a,"experience_id":"e"+a,"snapshot_at":"2026-08-29T00:00:00+00:00","condition_vector":(),"temporal_vector":(),"condition_hash":"a"*64,"experience_hash":"b"*64,"lineage_hash":"c"*64,"horizon_seconds":60,"outcome_observed_at":"2026-08-29T00:01:00+00:00","return_fraction":.01,"return_percent":1.0,"outcome_hash":"d"*64,"learning_event_hash":"e"*64,"exact_interval":True}.items())),)\nclass T(unittest.TestCase):\n    def test_read(self):\n        with patch.object(m,"_backend",return_value=B()): rows=m.read_crypto_learned_case_history()\n        print("[ROWS]",len(rows)); print("[ASSETS]",tuple(x.asset for x in rows))\n        self.assertEqual(tuple(x.asset for x in rows),("BTC","ETH","SOL"))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-189 exact learned-case history readback certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_189_crypto_learned_case_exact_history_readback.py'; test=r/'test_oad_189_crypto_learned_case_exact_history_readback.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-189 CRYPTO LEARNED CASE EXACT HISTORY READBACK INSTALLER"); print("="*118); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_068_exact_postgresql_independent_readback.py', 'oad_188_crypto_verified_learned_case_postgresql_persistence.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in []:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_189_crypto_learned_case_exact_history_readback import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-189 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
