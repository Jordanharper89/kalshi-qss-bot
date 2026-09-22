from __future__ import annotations
import os,sys,subprocess
from pathlib import Path

def root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for c in (base,base/"kalshi-qss-bot",*base.parents):
            if (c/"qseries_v2").is_dir():
                return c
    raise RuntimeError("Could not locate Q Series repository")

def write_atomic(path,source):
    path.parent.mkdir(parents=True,exist_ok=True)
    compile(source,str(path),"exec")
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def run_test(r,p):
    z=subprocess.run([sys.executable,str(p)],cwd=str(r))
    if z.returncode:
        raise RuntimeError("Certification test failed: "+p.name)

REVISION='OAD_229_CRYPTO_PHYSICAL_ENTITY_RELATIONSHIP_MATERIALIZATION_IDENTITY_SAFE_V1'
EXPECTED_INSTALLER='build_oad_229_crypto_physical_entity_relationship_materialization_IDENTITY_SAFE.py'
MODULE_NAME='oad_229_crypto_physical_entity_relationship_materialization.py'
TEST_NAME='test_oad_229_crypto_physical_entity_relationship_materialization.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_continuous_learner.ocl_016_entity_learning import build_entity_learning_observation,verify_entity_learning_observation\nfrom qseries_v2.oracle_continuous_learner.ocl_017_entity_relationship import learn_entity_relationship,verify_entity_relationship_state\nfrom .oad_218_existing_ocl_state_hash_envelope import envelope\nfrom .oad_227_crypto_learned_case_asof_snapshot_boundary import capture_crypto_learned_case_snapshot\n\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass PhysicalEntityRelationshipMaterialization:\n    as_of_sequence:int\n    entity_observations:int\n    relationships:tuple\n    entity_relationship_state_hash:str|None\n    state:str\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef materialize_entity_relationship_state(root=None,per_asset_limit=512):\n    snap=capture_crypto_learned_case_snapshot(root,per_asset_limit)\n    observations=[];association={}\n    for seq,oid,source,observed,praw in snap.rows:\n        p=praw if isinstance(praw,dict) else dict(praw or ())\n        asset=str(p.get("asset") or "").upper()\n        evh=str(p.get("evidence_hash") or "");outh=str(p.get("outcome_hash") or "")\n        rv=p.get("return_fraction")\n        if not asset or len(evh)!=64 or len(outh)!=64 or rv is None:continue\n        ts=observed.isoformat() if hasattr(observed,"isoformat") else str(observed)\n        eo=build_entity_learning_observation(f"asset:{asset.lower()}","crypto_asset","realized_return",float(rv),ts,evh,outh)\n        if not verify_entity_learning_observation(eo):raise RuntimeError("OCL-016 entity observation failed verification")\n        observations.append(eo)\n        for row in tuple(p.get("condition_vector") or ()):\n            if not isinstance(row,(list,tuple)) or not row:continue\n            family=str(row[0]).strip().lower()\n            if not family:continue\n            key=(f"source_family:{family}",f"asset:{asset.lower()}","observed_condition_association")\n            association.setdefault(key,[]).append(True)\n    relationships=[]\n    for (src,tgt,typ),evidence in sorted(association.items()):\n        rel=learn_entity_relationship(src,tgt,typ,tuple(evidence))\n        if not verify_entity_relationship_state(rel):raise RuntimeError("OCL-017 relationship failed verification")\n        relationships.append(rel)\n    rels=tuple(relationships)\n    h=envelope("entity_relationship",rels).state_hash if rels else None\n    return PhysicalEntityRelationshipMaterialization(snap.as_of_sequence,len(observations),rels,h,"MATERIALIZED_NON_CAUSAL_ASSOCIATIONS" if rels else "HOLD_ENTITY_RELATIONSHIP_EVIDENCE_REQUIRED")\n'
TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_229_crypto_physical_entity_relationship_materialization as m\nROWS=((1,"o","s","t",{"asset":"BTC","evidence_hash":"a"*64,"outcome_hash":"b"*64,"return_fraction":.01,"condition_vector":(("bitcoin","fee",1,"HIGH"),("coinbase","spot",1,"OBSERVED"))}),)\nclass T(unittest.TestCase):\n    def test_noncausal_relationship(self):\n        snap=SimpleNamespace(as_of_sequence=1,rows=ROWS)\n        with patch.object(m,"capture_crypto_learned_case_snapshot",return_value=snap):\n            r=m.materialize_entity_relationship_state()\n        print("[STATE]",r.state,"[REL]",len(r.relationships),"[HASH]",r.entity_relationship_state_hash)\n        self.assertEqual(r.state,"MATERIALIZED_NON_CAUSAL_ASSOCIATIONS")\n        self.assertEqual(len(r.entity_relationship_state_hash),64)\n        self.assertTrue(all(x.relationship_type=="observed_condition_association" for x in r.relationships))\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-229 outcome-grounded non-causal entity relationship materialization certified")\n'

def main():
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED_INSTALLER}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    print("="*124);print(" OAD-229 CRYPTO PHYSICAL ENTITY-RELATIONSHIP MATERIALIZATION");print("="*124)
    print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=pkg/'oad_227_crypto_learned_case_asof_snapshot_boundary.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_218_existing_ocl_state_hash_envelope.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_016_entity_learning.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_017_entity_relationship.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    print("[PASS] installer identity verified")
    targets=[m,t]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        run_test(r,t)
        print('[PASS] OCL-016/OCL-017 reused unchanged')
        print('[PASS] relationship type is observed association, never causal influence')
        print('[PASS] probability=FALSE direction=FALSE execution=FALSE')
        print("[DONE] OAD-229 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
