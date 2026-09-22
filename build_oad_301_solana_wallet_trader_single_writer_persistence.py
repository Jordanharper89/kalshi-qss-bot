
from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-301'
TITLE='SOLANA WALLET/TRADER SINGLE-WRITER PERSISTENCE'
EXPECTED='build_oad_301_solana_wallet_trader_single_writer_persistence.py'
MODULE='oad_301_solana_wallet_trader_single_writer_persistence.py'
TEST='test_oad_301_solana_wallet_trader_single_writer_persistence.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_300_solana_wallet_trader_claim_normalization.py', ('def normalize_current_gmgn_wallet_trader_intelligence',)), ('qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py', ('def canonicalize_expansion_observation', 'PRODUCER', 'PRIORITY')), ('qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py', ('def exact_postgresql_readback', 'def _query_one')), ('qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py', ('def submit_observation_batch', 'def await_request'))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport hashlib,json\nfrom .oad_300_solana_wallet_trader_claim_normalization import normalize_current_gmgn_wallet_trader_intelligence\nfrom .oad_261_universal_expansion_source_single_writer_postgresql_persistence import PRODUCER,PRIORITY,canonicalize_expansion_observation\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\nBATCH_ID="oad301.gmgn.wallet-trader"\n@dataclass(frozen=True,slots=True)\nclass Raw:\n    source_id:str\n    provenance_hash:str\n    observed_at:object\n    observation_type:str\n    source_class:str\n    provider:str\n    subject:str\n    payload:dict\n    execution_authority:bool=False\n@dataclass(frozen=True,slots=True)\nclass WalletTraderPersistenceResult:\n    token_address:str\n    raw_observations:int\n    canonical_observations:int\n    already_present:int\n    committed_new:int\n    exact_readback:int\n    observation_ids:tuple\n    execution_authority:bool=False\ndef _h(x):\n    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\ndef persist_current_wallet_trader_intelligence(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=30.0):\n    root=Path(root or Path.cwd()).resolve()\n    x=normalize_current_gmgn_wallet_trader_intelligence(acquisition_timeout_seconds)\n    now=datetime.now(timezone.utc)\n    sections={\n        "holders":{"token_address":x.token_address,"row_count":x.holder_rows,"claims":[c.claim_payload for c in x.provider_claims if c.claim_kind=="holder"],"provider_claim_only":True},\n        "traders":{"token_address":x.token_address,"row_count":x.trader_rows,"claims":[c.claim_payload for c in x.provider_claims if c.claim_kind=="trader"],"provider_claim_only":True},\n    }\n    raw=[]\n    for kind,payload in sections.items():\n        sid=f"source.gmgn.solana.token.{x.token_address}.{kind}"\n        raw.append(Raw(sid,_h({"source_id":sid,"observed_at":now,"payload":payload}),now,"gmgn_solana_"+kind,"wallet_trader_intelligence","gmgn",x.token_address,payload,False))\n    can=tuple(canonicalize_expansion_observation(y,BATCH_ID) for y in raw)\n    backend=_backend(root); missing=[]; existing=0\n    for i,y in enumerate(can):\n        if _query_one(backend,y.observation_id,i) is None: missing.append(y)\n        else: existing+=1\n    committed=0\n    if missing:\n        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)\n        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))\n        accepted=tuple(e for e in events if getattr(e,"accepted",False) is True)\n        if len(accepted)!=len(missing): raise RuntimeError("wallet/trader single-writer commit mismatch")\n        committed=len(accepted)\n    ids=tuple(y.observation_id for y in can)\n    rows=tuple(exact_postgresql_readback(ids,root))\n    if len(rows)!=2: raise RuntimeError("wallet/trader exact PostgreSQL readback mismatch")\n    return WalletTraderPersistenceResult(x.token_address,2,2,existing,committed,2,ids,False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_301_solana_wallet_trader_single_writer_persistence import *\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=persist_current_wallet_trader_intelligence()\n        print("[PHYSICAL] token=",r.token_address); print("[PHYSICAL] already_present=",r.already_present); print("[PHYSICAL] committed_new=",r.committed_new); print("[PHYSICAL] exact_readback=",r.exact_readback); print("[PHYSICAL] observation_ids=",r.observation_ids)\n        self.assertEqual(r.raw_observations,2); self.assertEqual(r.canonical_observations,2); self.assertEqual(r.already_present+r.committed_new,2); self.assertEqual(r.exact_readback,2); self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-301 GMGN wallet/trader intelligence persisted through universal single writer")\n    print("[PASS] exact 2/2 observation-ID PostgreSQL readback certified")\n    print("[PASS] provider claims preserved without promotion to truth")\n'

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def checked_write(path, source):
    s=textwrap.dedent(source).lstrip()
    ast.parse(s, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    t=path.with_suffix(path.suffix+".tmp")
    t.write_text(s, encoding="utf-8", newline="\n")
    os.replace(t, path)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename identity mismatch")
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE
    test=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[ROOT]", r)

    for rel, markers in DEPENDENCIES:
        p=r/rel
        if not p.is_file():
            raise RuntimeError("dependency missing: "+rel)
        s=p.read_text(encoding="utf-8")
        ast.parse(s, filename=str(p))
        for marker in markers:
            if marker not in s:
                raise RuntimeError("exact dependency marker missing: "+rel+" -> "+marker)
        print("[PASS] exact dependency verified:", rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
    ):
        p=r/rel
        if not p.is_file():
            raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p, hashlib.sha256(p.read_bytes()).hexdigest()))

    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        checked_write(module, MODULE_SOURCE)
        checked_write(test, TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+module.stem+" import *"
        if exp not in lines:
            lines.append(exp)
        checked_write(init, "\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("frozen boundary changed: "+p.name)

        print("[PASS] module installed:", module.relative_to(r))
        print("[PASS] test installed:", test.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] provider labels remain claims, not Oracle truth")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
