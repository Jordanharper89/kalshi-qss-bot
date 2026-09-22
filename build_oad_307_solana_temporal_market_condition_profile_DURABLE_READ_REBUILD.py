from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-307"
TITLE="SOLANA TEMPORAL MARKET CONDITION PROFILE — DURABLE READ REBUILD"
EXPECTED='build_oad_307_solana_temporal_market_condition_profile_DURABLE_READ_REBUILD.py'
MODULE='oad_307_solana_temporal_market_condition_profile.py'
TEST='test_oad_307_solana_temporal_market_condition_profile.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_267_solana_pool_liquidity_historical_state.py', ('def read_solana_proven_history', 'refresh=True', 'source_ids required when refresh=False')), ('qseries_v2/oracle_adapters/independent/oad_270_solana_price_volume_liquidity_acceleration_conditions.py', ('def build_solana_acceleration_conditions', 'class SolanaAccelerationCondition'))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nfrom .oad_267_solana_pool_liquidity_historical_state import read_solana_proven_history\nfrom .oad_270_solana_price_volume_liquidity_acceleration_conditions import build_solana_acceleration_conditions\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\nDISCOVERY_SOURCE_ID="source.dex.solana.token_discovery.latest"\n\n@dataclass(frozen=True,slots=True)\nclass TemporalMarketConditionProfile:\n    token_address:str\n    queried_rows:int\n    pair_conditions:tuple\n    ready_pairs:int\n    evidence_state:str\n    queried_sources:tuple\n    durable_read_only:bool=True\n    probability:None=None\n    direction:None=None\n    execution_authority:bool=False\n\ndef _latest_discovered_token(root=None,per_source_limit=64):\n    history=read_solana_proven_history(\n        root=root,\n        source_ids=(DISCOVERY_SOURCE_ID,),\n        per_source_limit=per_source_limit,\n        refresh=False,\n    )\n    if not history.records:\n        raise RuntimeError(\n            "No durable Solana discovery history found. "\n            "OAD-307 will not force a new production write merely to read history."\n        )\n\n    # OAD-267 returns exact bounded history for this source. Select the latest\n    # observation by persisted observed_at/sequence identity without acquiring\n    # or writing anything new.\n    rows=sorted(\n        history.records,\n        key=lambda r: (\n            str(r.observed_at),\n            -1 if r.sequence_number is None else int(r.sequence_number),\n            str(r.observation_id),\n        ),\n        reverse=True,\n    )\n    for row in rows:\n        tokens=tuple(row.payload.get("tokens") or ())\n        if not tokens:\n            continue\n        first=tokens[0]\n        if isinstance(first,dict):\n            token=str(first.get("token_address") or "").strip()\n            if token:\n                return token,history\n    raise RuntimeError("Durable Solana discovery history contains no token identity")\n\ndef build_current_temporal_market_condition_profile(\n    root=None,\n    per_source_limit=64,\n):\n    token,discovery_history=_latest_discovered_token(\n        root=root,\n        per_source_limit=per_source_limit,\n    )\n\n    source_ids=(\n        DISCOVERY_SOURCE_ID,\n        "source.dex.solana.token_pools."+token,\n        "source.onchain.solana.mint."+token,\n    )\n    history=read_solana_proven_history(\n        root=root,\n        source_ids=source_ids,\n        per_source_limit=per_source_limit,\n        refresh=False,\n    )\n\n    # Acceleration conditions consume the exact durable pool-history records.\n    # Discovery/mint records may coexist in the readback but are ignored by\n    # the underlying pool delta/pressure builders when not applicable.\n    conditions=build_solana_acceleration_conditions(history.records)\n    ready=sum(1 for x in conditions if x.state=="COMPOSITE_READY")\n    state=(\n        "TEMPORAL_READY"\n        if conditions and ready\n        else "TEMPORAL_PARTIAL"\n        if conditions\n        else "DURABLE_HISTORY_INSUFFICIENT_FOR_TEMPORAL_PAIR"\n    )\n    return TemporalMarketConditionProfile(\n        token_address=token,\n        queried_rows=history.queried_rows,\n        pair_conditions=conditions,\n        ready_pairs=ready,\n        evidence_state=state,\n        queried_sources=history.queried_sources,\n        durable_read_only=True,\n        probability=None,\n        direction=None,\n        execution_authority=False,\n    )\n'
TEST_SOURCE='import unittest\n\nfrom qseries_v2.oracle_adapters.independent.oad_307_solana_temporal_market_condition_profile import (\n    DISCOVERY_SOURCE_ID,\n    build_current_temporal_market_condition_profile,\n)\n\nclass T(unittest.TestCase):\n    def test_physical_durable_read_only(self):\n        x=build_current_temporal_market_condition_profile()\n        print("[PHYSICAL] token=",x.token_address)\n        print("[PHYSICAL] queried_rows=",x.queried_rows)\n        print("[PHYSICAL] queried_sources=",x.queried_sources)\n        print("[PHYSICAL] pair_conditions=",len(x.pair_conditions))\n        print("[PHYSICAL] ready_pairs=",x.ready_pairs)\n        print("[PHYSICAL] evidence_state=",x.evidence_state)\n        print("[PHYSICAL] durable_read_only=",x.durable_read_only)\n\n        self.assertTrue(x.token_address)\n        self.assertGreaterEqual(x.queried_rows,1)\n        self.assertIn(DISCOVERY_SOURCE_ID,x.queried_sources)\n        self.assertIn(\n            "source.dex.solana.token_pools."+x.token_address,\n            x.queried_sources,\n        )\n        self.assertIn(\n            "source.onchain.solana.mint."+x.token_address,\n            x.queried_sources,\n        )\n        self.assertTrue(x.durable_read_only)\n        self.assertIsNone(x.probability)\n        self.assertIsNone(x.direction)\n        self.assertFalse(x.execution_authority)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OAD-307 exact durable PostgreSQL history read physically certified")\n    print("[PASS] no refresh acquisition or production write required")\n    print("[PASS] probability=FALSE direction=FALSE execution=FALSE")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(p,s):
    s=textwrap.dedent(s).lstrip()
    ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp")
    q.write_text(s,encoding="utf-8",newline="\n")
    os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer filename identity mismatch")
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"
    print("="*120)
    print(" OAD-307 SOLANA TEMPORAL MARKET CONDITION PROFILE — DURABLE READ REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)
    for rel,marks in DEPENDENCIES:
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        s=p.read_text(encoding="utf-8")
        ast.parse(s,filename=str(p))
        for mark in marks:
            if mark not in s:
                raise RuntimeError("exact dependency marker missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
    ):
        p=r/rel
        if not p.is_file(): raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        write(m,MODULE_SOURCE)
        write(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] failed OAD-307 implementation replaced in place")
        print("[PASS] OAD-267 invoked with refresh=FALSE and exact source_ids")
        print("[PASS] no OAD-266 persistence cycle required for historical read")
        print("[PASS] module installed:",m.relative_to(r))
        print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-307 DURABLE READ REBUILD INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise
if __name__=="__main__":
    main()
