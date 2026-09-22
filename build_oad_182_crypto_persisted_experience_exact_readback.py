from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_182_CRYPTO_PERSISTED_EXPERIENCE_EXACT_READBACK_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import CanonicalPersistenceQueryRequest\nfrom .oad_068_exact_postgresql_independent_readback import _backend\nfrom .oad_179_crypto_experience_candidate_postgresql_persistence import SOURCE_PREFIX\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\nASSETS=("BTC","ETH","SOL")\nDEFAULT_PER_ASSET_LIMIT=256\n\n@dataclass(frozen=True,slots=True)\nclass PersistedCryptoExperience:\n    observation_id:str\n    source_id:str\n    experience_id:str\n    asset:str\n    snapshot_at:str\n    cohort_state:str\n    condition_vector:tuple\n    temporal_vector:tuple\n    evidence_hash:str\n    condition_hash:str\n    experience_hash:str\n    lineage_hash:str\n    outcome_attached:bool\n    observed_at:str\n\n@dataclass(frozen=True,slots=True)\nclass PersistedCryptoExperienceReadback:\n    queried_assets:int\n    queried_rows:int\n    experiences:int\n    records:tuple\n    read_only:bool=True\n\ndef _record(row):\n    if row.observation_type!="crypto_historical_experience_candidate": return None\n    p=dict(row.payload)\n    if bool(p.get("outcome_attached",False)): return None\n    return PersistedCryptoExperience(\n        str(row.observation_id),str(row.source_id),str(p["experience_id"]),str(p["asset"]),\n        str(p["snapshot_at"]),str(p["cohort_state"]),tuple(p["condition_vector"]),\n        tuple(p["temporal_vector"]),str(p["evidence_hash"]),str(p["condition_hash"]),\n        str(p["experience_hash"]),str(p["lineage_hash"]),False,row.observed_at.isoformat()\n    )\n\ndef read_persisted_crypto_experiences(root=None,assets=ASSETS,per_asset_limit=DEFAULT_PER_ASSET_LIMIT):\n    root=Path(root or Path.cwd()).resolve()\n    backend=_backend(root)\n    rows=[]\n    for i,asset in enumerate(tuple(assets)):\n        source_id=f"{SOURCE_PREFIX}{str(asset).lower()}"\n        req=CanonicalPersistenceQueryRequest.by_source_id(\n            query_id=f"query.oad182.crypto-experience.{i}.{str(asset).lower()}",\n            backend_id=backend.backend_id,\n            source_id=source_id,\n            limit=int(per_asset_limit),\n            requested_at=datetime.now(timezone.utc),\n            query_metadata={"read_only":True,"build_id":"OAD-182","query_mode":"exact_experience_source_id"},\n        )\n        rows.extend(tuple(backend.query(request=req)))\n    recs=tuple(x for x in (_record(r) for r in rows) if x is not None)\n    recs=tuple(sorted(recs,key=lambda x:(x.snapshot_at,x.asset,x.experience_id)))\n    return PersistedCryptoExperienceReadback(len(tuple(assets)),len(rows),len(recs),recs,True)\n'
TEST_SOURCE='import unittest\nfrom datetime import datetime,timezone\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_182_crypto_persisted_experience_exact_readback as m\nclass Fake:\n    backend_id="fake"\n    def __init__(self): self.requests=[]\n    def query(self,request):\n        self.requests.append(request)\n        asset=request.source_id.rsplit(".",1)[-1].upper()\n        return (SimpleNamespace(\n            observation_id="obs-"+asset,source_id=request.source_id,\n            observation_type="crypto_historical_experience_candidate",\n            observed_at=datetime(2026,8,29,2,0,0,tzinfo=timezone.utc),\n            payload=tuple({\n                "experience_id":"exp-"+asset,"asset":asset,"snapshot_at":"2026-08-29T02:00:00+00:00",\n                "cohort_state":"FULL_COVERAGE","condition_vector":(("coinbase","spot_price",100.0,"OBSERVED"),),\n                "temporal_vector":(("coinbase","spot_price","INCREASED",1.0,1.0,True),),\n                "evidence_hash":"a"*64,"condition_hash":"b"*64,"experience_hash":"c"*64,\n                "lineage_hash":"d"*64,"outcome_attached":False\n            }.items())\n        ),)\nclass T(unittest.TestCase):\n    def test_exact_sources(self):\n        b=Fake()\n        with patch.object(m,"_backend",return_value=b):\n            r=m.read_persisted_crypto_experiences(assets=("BTC","ETH","SOL"),per_asset_limit=16)\n        print("[QUERY_TYPES]",tuple(x.query_type for x in b.requests))\n        print("[SOURCES]",tuple(x.source_id for x in b.requests))\n        print("[EXPERIENCES]",r.experiences)\n        self.assertEqual(r.experiences,3)\n        self.assertTrue(all(x.query_type=="by_source_id" for x in b.requests))\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-182 exact persisted crypto experience readback certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_182_crypto_persisted_experience_exact_readback.py'; test=r/'test_oad_182_crypto_persisted_experience_exact_readback.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-182 CRYPTO PERSISTED EXPERIENCE EXACT READBACK INSTALLER"); print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_068_exact_postgresql_independent_readback.py', 'oad_179_crypto_experience_candidate_postgresql_persistence.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in []:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_182_crypto_persisted_experience_exact_readback import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-182 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
