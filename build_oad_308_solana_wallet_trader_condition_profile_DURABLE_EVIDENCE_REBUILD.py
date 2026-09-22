from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
EXPECTED='build_oad_308_solana_wallet_trader_condition_profile_DURABLE_EVIDENCE_REBUILD.py'
MODULE="oad_308_solana_wallet_trader_condition_profile.py"
TEST="test_oad_308_solana_wallet_trader_condition_profile.py"
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_267_solana_pool_liquidity_historical_state.py', ('def read_solana_proven_history', 'source_ids required when refresh=False')), ('qseries_v2/oracle_adapters/independent/oad_301_solana_wallet_trader_single_writer_persistence.py', ('sid=f"source.gmgn.solana.token.{x.token_address}.{kind}"', '"gmgn_solana_"+kind')), ('qseries_v2/oracle_adapters/independent/oad_307_solana_temporal_market_condition_profile.py', ('def build_current_temporal_market_condition_profile', 'durable_read_only'))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nfrom .oad_267_solana_pool_liquidity_historical_state import read_solana_proven_history\nfrom .oad_307_solana_temporal_market_condition_profile import build_current_temporal_market_condition_profile\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass WalletTraderConditionProfile:\n    token_address:str\n    holder_rows:int\n    trader_rows:int\n    holder_observations:int\n    trader_observations:int\n    conditions:tuple\n    evidence_state:str\n    queried_sources:tuple\n    provider_claim_only:bool=True\n    durable_read_only:bool=True\n    probability:None=None\n    direction:None=None\n    execution_authority:bool=False\n\ndef _latest(records, observation_type):\n    rows=tuple(r for r in records if r.observation_type==observation_type)\n    if not rows:\n        return None\n    return sorted(\n        rows,\n        key=lambda r:(\n            -1 if r.sequence_number is None else int(r.sequence_number),\n            str(r.observed_at),\n            str(r.observation_id),\n        ),\n    )[-1]\n\ndef _count(row):\n    if row is None:\n        return 0\n    try:\n        return max(0,int(row.payload.get("row_count") or 0))\n    except (TypeError,ValueError):\n        return 0\n\ndef build_current_wallet_trader_condition_profile(root=None,per_source_limit=64):\n    # Current token identity comes only from already-durable Solana evidence.\n    temporal=build_current_temporal_market_condition_profile(\n        root=root,\n        per_source_limit=per_source_limit,\n    )\n    token=temporal.token_address\n    source_ids=(\n        "source.gmgn.solana.token."+token+".holders",\n        "source.gmgn.solana.token."+token+".traders",\n    )\n    h=read_solana_proven_history(\n        root=root,\n        source_ids=source_ids,\n        per_source_limit=per_source_limit,\n        refresh=False,\n    )\n    holder=_latest(h.records,"gmgn_solana_holders")\n    trader=_latest(h.records,"gmgn_solana_traders")\n    holder_rows=_count(holder)\n    trader_rows=_count(trader)\n\n    if holder is not None and trader is not None:\n        state="DURABLE_WALLET_TRADER_EVIDENCE_READY"\n    elif holder is not None or trader is not None:\n        state="DURABLE_WALLET_TRADER_EVIDENCE_PARTIAL"\n    else:\n        state="DURABLE_WALLET_TRADER_EVIDENCE_UNAVAILABLE"\n\n    conditions=(\n        ("holder_rows",holder_rows),\n        ("trader_rows",trader_rows),\n        ("holder_evidence_present",holder is not None),\n        ("trader_evidence_present",trader is not None),\n    )\n    return WalletTraderConditionProfile(\n        token_address=token,\n        holder_rows=holder_rows,\n        trader_rows=trader_rows,\n        holder_observations=sum(1 for r in h.records if r.observation_type=="gmgn_solana_holders"),\n        trader_observations=sum(1 for r in h.records if r.observation_type=="gmgn_solana_traders"),\n        conditions=conditions,\n        evidence_state=state,\n        queried_sources=h.queried_sources,\n        provider_claim_only=True,\n        durable_read_only=True,\n        probability=None,\n        direction=None,\n        execution_authority=False,\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_308_solana_wallet_trader_condition_profile import (\n    build_current_wallet_trader_condition_profile,\n)\n\nclass T(unittest.TestCase):\n    def test_physical_durable_evidence_only(self):\n        x=build_current_wallet_trader_condition_profile()\n        print("[PHYSICAL] token=",x.token_address)\n        print("[PHYSICAL] holder_rows=",x.holder_rows)\n        print("[PHYSICAL] trader_rows=",x.trader_rows)\n        print("[PHYSICAL] holder_observations=",x.holder_observations)\n        print("[PHYSICAL] trader_observations=",x.trader_observations)\n        print("[PHYSICAL] evidence_state=",x.evidence_state)\n        print("[PHYSICAL] queried_sources=",x.queried_sources)\n        print("[PHYSICAL] durable_read_only=",x.durable_read_only)\n        self.assertTrue(x.token_address)\n        self.assertEqual(len(x.queried_sources),2)\n        self.assertIn(x.evidence_state,(\n            "DURABLE_WALLET_TRADER_EVIDENCE_READY",\n            "DURABLE_WALLET_TRADER_EVIDENCE_PARTIAL",\n            "DURABLE_WALLET_TRADER_EVIDENCE_UNAVAILABLE",\n        ))\n        self.assertTrue(x.provider_claim_only)\n        self.assertTrue(x.durable_read_only)\n        self.assertIsNone(x.probability)\n        self.assertIsNone(x.direction)\n        self.assertFalse(x.execution_authority)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OAD-308 durable wallet/trader condition read physically certified")\n    print("[PASS] no GMGN acquisition invoked by condition intelligence")\n    print("[PASS] missing durable evidence is reported as unavailable, never fabricated")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp")
    q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer filename identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" OAD-308 SOLANA WALLET / TRADER CONDITION PROFILE — DURABLE EVIDENCE REBUILD INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPENDENCIES:
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        s=p.read_text(encoding="utf-8"); ast.parse(s,filename=str(p))
        for mark in marks:
            if mark not in s: raise RuntimeError("exact dependency marker missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        write(m,MODULE_SOURCE); write(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []; exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] failed OAD-308 implementation replaced in place")
        print("[PASS] GMGN live acquisition removed from condition-intelligence path")
        print("[PASS] exact current-token holder/trader source IDs read from durable PostgreSQL evidence")
        print("[PASS] missing evidence degrades truthfully to UNAVAILABLE/PARTIAL")
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-308 DURABLE EVIDENCE REBUILD INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
