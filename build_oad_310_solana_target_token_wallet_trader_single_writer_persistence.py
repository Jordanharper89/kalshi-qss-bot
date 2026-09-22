from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
EXPECTED='build_oad_310_solana_target_token_wallet_trader_single_writer_persistence.py'
MODULE="oad_310_solana_target_token_wallet_trader_single_writer_persistence.py"
TEST="test_oad_310_solana_target_token_wallet_trader_single_writer_persistence.py"
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_309_solana_target_token_wallet_trader_coverage_acquisition.py', ('def acquire_target_token_wallet_trader_coverage', 'RATE_LIMITED_HOLD', 'provider_claim_only')), ('qseries_v2/oracle_adapters/independent/oad_301_solana_wallet_trader_single_writer_persistence.py', ('sid=f"source.gmgn.solana.token.{x.token_address}.{kind}"', '"gmgn_solana_"+kind', 'provider_claim_only')), ('qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py', ('def canonicalize_expansion_observation', 'PRODUCER', 'PRIORITY')), ('qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py', ('def exact_postgresql_readback', 'def _query_one')), ('qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py', ('def submit_observation_batch', 'def await_request'))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport hashlib,json\n\nfrom .oad_309_solana_target_token_wallet_trader_coverage_acquisition import acquire_target_token_wallet_trader_coverage\nfrom .oad_261_universal_expansion_source_single_writer_postgresql_persistence import PRODUCER,PRIORITY,canonicalize_expansion_observation\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\nBATCH_ID="oad310.gmgn.target-token.wallet-trader"\n\n@dataclass(frozen=True,slots=True)\nclass Raw:\n    source_id:str\n    provenance_hash:str\n    observed_at:object\n    observation_type:str\n    source_class:str\n    provider:str\n    subject:str\n    payload:dict\n    execution_authority:bool=False\n\n@dataclass(frozen=True,slots=True)\nclass TargetTokenWalletTraderPersistenceResult:\n    token_address:str\n    acquisition_state:str\n    raw_observations:int\n    canonical_observations:int\n    already_present:int\n    committed_new:int\n    exact_readback:int\n    observation_ids:tuple\n    retry_after_seconds:float|None\n    persistence_state:str\n    execution_authority:bool=False\n\ndef _h(x):\n    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n\ndef persist_target_token_wallet_trader_coverage(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=30.0):\n    root=Path(root or Path.cwd()).resolve()\n    x=acquire_target_token_wallet_trader_coverage(root=root,timeout_seconds=acquisition_timeout_seconds)\n\n    # A provider-wide rate-limit HOLD is not evidence and must never be persisted.\n    if x.state=="RATE_LIMITED_HOLD":\n        return TargetTokenWalletTraderPersistenceResult(\n            x.token_address,x.state,0,0,0,0,0,(),\n            x.retry_after_seconds,"RATE_LIMITED_HOLD_NO_WRITE",False\n        )\n    if x.state!="ACQUIRED":\n        raise RuntimeError("unsupported target-token acquisition state: "+str(x.state))\n\n    now=datetime.now(timezone.utc)\n    sections={\n        "holders":{\n            "token_address":x.token_address,\n            "row_count":x.holder_rows,\n            "claims":[c.claim_payload for c in x.provider_claims if c.claim_kind=="holder"],\n            "provider_claim_only":True,\n        },\n        "traders":{\n            "token_address":x.token_address,\n            "row_count":x.trader_rows,\n            "claims":[c.claim_payload for c in x.provider_claims if c.claim_kind=="trader"],\n            "provider_claim_only":True,\n        },\n    }\n    raw=[]\n    for kind,payload in sections.items():\n        sid=f"source.gmgn.solana.token.{x.token_address}.{kind}"\n        raw.append(Raw(\n            sid,\n            _h({"source_id":sid,"observed_at":now,"payload":payload}),\n            now,\n            "gmgn_solana_"+kind,\n            "wallet_trader_intelligence",\n            "gmgn",\n            x.token_address,\n            payload,\n            False,\n        ))\n\n    can=tuple(canonicalize_expansion_observation(y,BATCH_ID) for y in raw)\n    backend=_backend(root); missing=[]; existing=0\n    for i,y in enumerate(can):\n        if _query_one(backend,y.observation_id,i) is None:\n            missing.append(y)\n        else:\n            existing+=1\n\n    committed=0\n    if missing:\n        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)\n        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))\n        accepted=tuple(e for e in events if getattr(e,"accepted",False) is True)\n        if len(accepted)!=len(missing):\n            raise RuntimeError("target-token wallet/trader single-writer commit mismatch")\n        committed=len(accepted)\n\n    ids=tuple(y.observation_id for y in can)\n    rows=tuple(exact_postgresql_readback(ids,root))\n    if len(rows)!=2:\n        raise RuntimeError("target-token wallet/trader exact PostgreSQL readback mismatch")\n\n    return TargetTokenWalletTraderPersistenceResult(\n        x.token_address,x.state,2,2,existing,committed,2,ids,None,\n        "PERSISTED_EXACT_TARGET_TOKEN_EVIDENCE",False\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_310_solana_target_token_wallet_trader_single_writer_persistence import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        x=persist_target_token_wallet_trader_coverage()\n        print("[PHYSICAL] token=",x.token_address)\n        print("[PHYSICAL] acquisition_state=",x.acquisition_state)\n        print("[PHYSICAL] persistence_state=",x.persistence_state)\n        print("[PHYSICAL] raw_observations=",x.raw_observations)\n        print("[PHYSICAL] canonical_observations=",x.canonical_observations)\n        print("[PHYSICAL] already_present=",x.already_present)\n        print("[PHYSICAL] committed_new=",x.committed_new)\n        print("[PHYSICAL] exact_readback=",x.exact_readback)\n        print("[PHYSICAL] retry_after_seconds=",x.retry_after_seconds)\n        print("[PHYSICAL] observation_ids=",x.observation_ids)\n        self.assertTrue(x.token_address)\n        self.assertFalse(x.execution_authority)\n        if x.acquisition_state=="RATE_LIMITED_HOLD":\n            self.assertEqual(x.persistence_state,"RATE_LIMITED_HOLD_NO_WRITE")\n            self.assertEqual(x.raw_observations,0)\n            self.assertEqual(x.canonical_observations,0)\n            self.assertEqual(x.committed_new,0)\n            self.assertEqual(x.exact_readback,0)\n            self.assertEqual(x.observation_ids,())\n            self.assertGreaterEqual(x.retry_after_seconds,1.0)\n        else:\n            self.assertEqual(x.acquisition_state,"ACQUIRED")\n            self.assertEqual(x.persistence_state,"PERSISTED_EXACT_TARGET_TOKEN_EVIDENCE")\n            self.assertEqual(x.raw_observations,2)\n            self.assertEqual(x.canonical_observations,2)\n            self.assertEqual(x.already_present+x.committed_new,2)\n            self.assertEqual(x.exact_readback,2)\n            self.assertEqual(len(x.observation_ids),2)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-310 target-token wallet/trader persistence boundary physically certified")\n    print("[PASS] ACQUIRED evidence uses universal single writer + exact PostgreSQL readback")\n    print("[PASS] RATE_LIMITED_HOLD performs zero persistence writes")\n    print("[PASS] provider claims remain claims; probability/direction/publication/execution disabled")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(p,s):
    s=textwrap.dedent(s).lstrip();ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix(p.suffix+".tmp")
    q.write_text(s,encoding="utf-8",newline="\n");os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED:raise RuntimeError("installer filename identity mismatch")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE;t=r/TEST;init=pkg/"__init__.py"
    print("="*120);print(" OAD-310 SOLANA TARGET-TOKEN WALLET/TRADER SINGLE-WRITER PERSISTENCE INSTALLER");print("="*120);print("[ROOT]",r)
    for rel,marks in DEPENDENCIES:
        p=r/rel
        if not p.is_file():raise RuntimeError("dependency missing: "+rel)
        s=p.read_text(encoding="utf-8");ast.parse(s,filename=str(p))
        for mark in marks:
            if mark not in s:raise RuntimeError("exact dependency marker missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
        p=r/rel
        if not p.is_file():raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        write(m,MODULE_SOURCE);write(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else [];exp="from ."+m.stem+" import *"
        if exp not in lines:lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] OAD-309 exact target-token acquisition bound")
        print("[PASS] OAD-301 certified source-ID/payload semantics preserved")
        print("[PASS] ACQUIRED evidence routes through OAD-261 + OPH-019 universal single writer")
        print("[PASS] exact observation-ID PostgreSQL readback required")
        print("[PASS] RATE_LIMITED_HOLD creates zero canonical observations and zero writes")
        print("[PASS] module installed:",m.relative_to(r));print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-310 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise
if __name__=="__main__":main()
