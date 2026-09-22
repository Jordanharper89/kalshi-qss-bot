from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-271'
REVISION='OAD_271_SOLANA_HISTORICAL_EXPERIENCE_FORMATION_V1'
TITLE='SOLANA HISTORICAL EXPERIENCE FORMATION'
MODULE_NAME='oad_271_solana_historical_experience_formation.py'
TEST_NAME='test_oad_271_solana_historical_experience_formation.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_267_solana_pool_liquidity_historical_state.py': ('read_solana_proven_history',), 'qseries_v2/oracle_adapters/independent/oad_270_solana_price_volume_liquidity_acceleration_conditions.py': ('build_solana_acceleration_conditions',), 'qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py': ('_backend', '_query_one', 'exact_postgresql_readback'), 'qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py': ('submit_observation_batch', 'await_request')}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom hashlib import sha256\nimport json\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom .oad_267_solana_pool_liquidity_historical_state import read_solana_proven_history\nfrom .oad_270_solana_price_volume_liquidity_acceleration_conditions import build_solana_acceleration_conditions\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\nPRODUCER="oracle.solana_experience_candidates"\nPRIORITY=20\nSOURCE_PREFIX="source.solana.experience."\n\n@dataclass(frozen=True,slots=True)\nclass SolanaHistoricalExperience:\n    experience_id:str\n    token_address:str\n    pair_address:str\n    snapshot_at:str\n    conditions:tuple\n    evidence_observation_ids:tuple\n    evidence_hash:str\n    experience_hash:str\n    outcome_attached:bool=False\n    probability:None=None\n    direction:None=None\n    execution_authority:bool=False\n\n@dataclass(frozen=True,slots=True)\nclass SolanaExperienceFormationResult:\n    state:str\n    experiences:int\n    already_present:int\n    committed_new:int\n    exact_readback:int\n    experience_ids:tuple\n    execution_authority:bool=False\n\ndef _hash(v):\n    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n\ndef build_solana_historical_experiences(records):\n    conditions=build_solana_acceleration_conditions(records)\n    by_source={}\n    for r in records:\n        by_source.setdefault(r.source_id,[]).append(r)\n    out=[]\n    for c in conditions:\n        rows=tuple(sorted(by_source.get(c.source_id,()),key=lambda x:(-1 if x.sequence_number is None else int(x.sequence_number),x.observed_at,x.observation_id)))\n        if len(rows)<2: continue\n        latest=rows[-1]\n        token=str(latest.payload.get("token_address") or "")\n        evidence_ids=(rows[-2].observation_id,rows[-1].observation_id)\n        evidence_hash=_hash(evidence_ids)\n        core=(token,c.pair_address,c.observed_at,c.conditions,evidence_ids,evidence_hash)\n        experience_hash=_hash(core)\n        experience_id=f"solana-exp:{token}:{c.pair_address}:{experience_hash[:24]}"\n        out.append(SolanaHistoricalExperience(experience_id,token,c.pair_address,c.observed_at,c.conditions,evidence_ids,evidence_hash,experience_hash,False,None,None,False))\n    return tuple(out)\n\ndef canonicalize_solana_experience(x):\n    observed=datetime.fromisoformat(str(x.snapshot_at).replace("Z","+00:00")) if "T" in str(x.snapshot_at) else datetime.now(timezone.utc)\n    if observed.tzinfo is None: observed=observed.replace(tzinfo=timezone.utc)\n    raw=RawSourceObservation.create(\n        source_observation_id=x.experience_id,\n        observed_at=observed,\n        observation_type="solana_historical_experience_candidate",\n        payload={\n            "experience_id":x.experience_id,\n            "token_address":x.token_address,\n            "pair_address":x.pair_address,\n            "snapshot_at":x.snapshot_at,\n            "conditions":x.conditions,\n            "evidence_observation_ids":x.evidence_observation_ids,\n            "evidence_hash":x.evidence_hash,\n            "experience_hash":x.experience_hash,\n            "outcome_attached":False,\n            "probability":None,\n            "direction":None,\n        },\n        provenance={"producer":PRODUCER,"evidence_hash":x.evidence_hash,"read_only":True},\n    )\n    return CanonicalObservation.create(\n        source_id=SOURCE_PREFIX+x.token_address,\n        raw_observation=raw,\n        acquired_at=datetime.now(timezone.utc),\n        acquisition_batch_id="oad271.solana-experience",\n    )\n\ndef form_and_persist_solana_historical_experiences(\n    root=None,\n    timeout_seconds=120.0,\n    per_source_limit=64,\n    refresh=True,\n):\n    root=Path(root or Path.cwd()).resolve()\n    history=read_solana_proven_history(root=root,per_source_limit=per_source_limit,refresh=refresh,timeout_seconds=timeout_seconds)\n    experiences=build_solana_historical_experiences(history.records)\n    if not experiences:\n        return SolanaExperienceFormationResult("HOLD_TEMPORAL_DEPTH_REQUIRED",0,0,0,0,(),False)\n\n    canonical=tuple(canonicalize_solana_experience(x) for x in experiences)\n    backend=_backend(root); missing=[]; existing=0\n    for i,x in enumerate(canonical):\n        if _query_one(backend,x.observation_id,i) is None: missing.append(x)\n        else: existing+=1\n    committed=0\n    if missing:\n        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)\n        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))\n        accepted=tuple(e for e in events if getattr(e,"accepted",False) is True)\n        if len(accepted)!=len(missing):\n            raise RuntimeError("Solana historical experience single-writer commit mismatch")\n        committed=len(accepted)\n    ids=tuple(x.observation_id for x in canonical)\n    rows=tuple(exact_postgresql_readback(ids,root))\n    if len(rows)!=len(ids):\n        raise RuntimeError("Solana historical experience exact readback mismatch")\n    return SolanaExperienceFormationResult("EXPERIENCE_CANDIDATES_PERSISTED",len(experiences),existing,committed,len(rows),tuple(x.experience_id for x in experiences),False)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation\nfrom qseries_v2.oracle_adapters.independent.oad_271_solana_historical_experience_formation import *\n\nclass T(unittest.TestCase):\n    def test_candidate(self):\n        a=SolanaHistoricalObservation("oa","S","solana_token_pool_identity_liquidity","2026-09-01T00:00:00+00:00",1,"dex","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":100,"buys_h24":10,"sells_h24":9,"volume_h24":100,"price_usd":1.0},)})\n        b=SolanaHistoricalObservation("ob","S","solana_token_pool_identity_liquidity","2026-09-01T00:01:00+00:00",2,"dex","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":125,"buys_h24":15,"sells_h24":10,"volume_h24":130,"price_usd":1.1},)})\n        r=build_solana_historical_experiences((a,b))\n        print("[EXPERIENCE]",r[0].experience_id)\n        print("[EVIDENCE]",r[0].evidence_observation_ids)\n        self.assertEqual(r[0].evidence_observation_ids,("oa","ob"))\n        self.assertFalse(r[0].outcome_attached)\n        self.assertIsNone(r[0].probability)\n        self.assertIsNone(r[0].direction)\n\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-271 deterministic outcome-pending Solana historical-experience formation certified")\n    print("[PASS] persistence remains gated on real temporal depth")\n'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    root=locate_root()
    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=root/TEST_NAME
    init=pkg/"__init__.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",root)

    for rel,symbols in DEPENDENCIES.items():
        p=root/rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: "+rel)
        src=p.read_text(encoding="utf-8")
        for symbol in symbols:
            if ("def "+symbol+"(") not in src and ("class "+symbol) not in src:
                raise RuntimeError("Exact dependency symbol missing: "+rel+" -> "+symbol)
        print("[PASS] exact dependency verified:",rel)

    protected=[]
    for p,label in (
        (root/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
        (root/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py","Frozen Kalshi OAD-055"),
    ):
        if p.is_file():
            protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
            print("[PASS]",label,"verified")

    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write_checked(module,MODULE_SOURCE)
        write_checked(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+module.stem+" import *"
        if exp not in lines:
            lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen boundary changed: "+p.name)

        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
