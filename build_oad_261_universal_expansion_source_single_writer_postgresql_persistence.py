
from __future__ import annotations
import ast, hashlib, os, subprocess, sys, textwrap
from pathlib import Path

BUILD_ID = 'OAD-261'
REVISION = 'OAD_261_UNIVERSAL_EXPANSION_SOURCE_SINGLE_WRITER_POSTGRESQL_PERSISTENCE_AND_EXACT_READBACK_V1'
TITLE = 'UNIVERSAL EXPANSION SOURCE SINGLE-WRITER POSTGRESQL PERSISTENCE AND EXACT READBACK'
MODULE_NAME = 'oad_261_universal_expansion_source_single_writer_postgresql_persistence.py'
TEST_NAME = 'test_oad_261_universal_expansion_source_single_writer_postgresql_persistence.py'
DEPENDENCIES = ['qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py', 'qseries_v2/oracle_adapters/independent/oad_257_coinbase_orderbook_physical_live_acquisition_certification.py', 'qseries_v2/oracle_adapters/independent/oad_258_solana_dex_liquidity_physical_live_acquisition_certification.py', 'qseries_v2/oracle_adapters/independent/oad_259_solana_stablecoin_physical_live_acquisition_certification.py', 'qseries_v2/oracle_adapters/independent/oad_260_derivatives_open_interest_funding_physical_resilient_certification.py', 'qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py', 'qseries_v2/oracle_intelligence/live_acquisition/oracle_live_read_only_acquisition_runtime.py']
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom .oad_253_coinbase_exchange_liquidity_orderbook_intelligence import acquire_coinbase_orderbook\nfrom .oad_254_solana_dex_liquidity_intelligence import acquire_solana_dex_liquidity\nfrom .oad_255_solana_stablecoin_supply_intelligence import acquire_solana_stablecoin_supply\nfrom .oad_260_derivatives_open_interest_funding_physical_resilient_certification import acquire_resilient_derivatives_state\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\nPRODUCER="oracle.crypto_independent_expansion"; PRIORITY=20\ndef _dt(v):\n    if isinstance(v,datetime): return v if v.tzinfo else v.replace(tzinfo=timezone.utc)\n    d=datetime.fromisoformat(str(v).replace("Z","+00:00")); return d if d.tzinfo else d.replace(tzinfo=timezone.utc)\ndef canonicalize_expansion_observation(x,acquisition_batch_id):\n    raw=RawSourceObservation.create(source_observation_id=f"{x.source_id}:{x.provenance_hash}",observed_at=_dt(x.observed_at),observation_type=x.observation_type,payload={"source_class":x.source_class,"independent_evidence":True,"provider":x.provider,"subject":x.subject,"provenance_hash":x.provenance_hash,"observation_payload":dict(x.payload)},provenance={"provider":x.provider,"source_class":x.source_class,"independent_evidence":True,"read_only":True})\n    return CanonicalObservation.create(source_id=x.source_id,raw_observation=raw,acquired_at=datetime.now(timezone.utc),acquisition_batch_id=str(acquisition_batch_id))\ndef acquire_live_expansion_observations(timeout_seconds=20.0):\n    derivatives,_,_=acquire_resilient_derivatives_state("BTCUSDT",timeout_seconds)\n    return (acquire_coinbase_orderbook("BTC-USD",2,timeout_seconds),acquire_solana_dex_liquidity("SOL/USDC",25,timeout_seconds),acquire_solana_stablecoin_supply("USDC",timeout_seconds),derivatives)\n@dataclass(frozen=True,slots=True)\nclass ExpansionPersistenceResult:\n    raw_observations:int; canonical_observations:int; already_present:int; committed_new:int; exact_readback:int; providers:tuple; source_ids:tuple; observation_ids:tuple; rows:tuple; execution_authority:bool=False\ndef persist_live_expansion_sources(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):\n    root=Path(root or Path.cwd()).resolve(); raw=tuple(acquire_live_expansion_observations(acquisition_timeout_seconds)); canonical=tuple(canonicalize_expansion_observation(x,"oad261.crypto-independent-expansion") for x in raw)\n    backend=_backend(root); existing=0; missing=[]\n    for i,x in enumerate(canonical):\n        if _query_one(backend,x.observation_id,i) is None: missing.append(x)\n        else: existing+=1\n    committed=0\n    if missing:\n        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root); events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds))); accepted=tuple(x for x in events if getattr(x,"accepted",False) is True)\n        if len(accepted)!=len(missing): raise RuntimeError("expansion-source universal single-writer commit mismatch")\n        committed=len(accepted)\n    ids=tuple(x.observation_id for x in canonical); rows=tuple(exact_postgresql_readback(ids,root)) if ids else ()\n    if len(rows)!=len(ids): raise RuntimeError("expansion-source exact PostgreSQL readback mismatch")\n    return ExpansionPersistenceResult(len(raw),len(canonical),existing,committed,len(rows),tuple(x.provider for x in raw),tuple(x.source_id for x in raw),ids,rows,False)\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  r=persist_live_expansion_sources()\n  print("[PHYSICAL] raw_observations=",r.raw_observations); print("[PHYSICAL] canonical_observations=",r.canonical_observations); print("[PHYSICAL] already_present=",r.already_present); print("[PHYSICAL] committed_new=",r.committed_new); print("[PHYSICAL] exact_readback=",r.exact_readback); print("[PHYSICAL] providers=",r.providers); print("[PHYSICAL] source_ids=",r.source_ids)\n  self.assertEqual(r.raw_observations,4); self.assertEqual(r.canonical_observations,4); self.assertEqual(r.exact_readback,4); self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-261 live expansion sources persisted through OPH-019 single writer"); print("[PASS] exact by-observation-ID PostgreSQL readback certified"); print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")\n'

def locate_root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    root=locate_root()
    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=root/TEST_NAME
    init=pkg/"__init__.py"
    freeze=root/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py"
    kalshi=root/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",root)

    for rel in DEPENDENCIES:
        p=root/rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: "+rel)
        print("[PASS] dependency verified:",rel)

    frozen={}
    for p,label in ((freeze,"Frozen OPH-023"),(kalshi,"Frozen Kalshi OAD-055")):
        if p.is_file():
            frozen[p]=hashlib.sha256(p.read_bytes()).hexdigest()
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

        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)

        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
