from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_160_ETHEREUM_ONCHAIN_CANONICAL_POSTGRESQL_PERSISTENCE_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_160_ethereum_onchain_canonical_postgresql_persistence.py'; test=r/'test_oad_160_ethereum_onchain_canonical_postgresql_persistence.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-160 ETHEREUM ON-CHAIN CANONICAL POSTGRESQL PERSISTENCE INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_068_exact_postgresql_independent_readback.py', 'oad_158_ethereum_finalized_chain_block_acquisition.py', 'oad_159_ethereum_fee_transaction_pressure_acquisition.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    if 160>=160:
        canonical=r/"qseries_v2"/"oracle_intelligence"/"live_acquisition"/"oracle_live_read_only_acquisition_runtime.py"
        oph=r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
        if not canonical.is_file(): raise RuntimeError("Canonical observation runtime missing")
        if not oph.is_file(): raise RuntimeError("OPH-019 universal PostgreSQL queue missing")
        print("[PASS] exact canonical observation runtime verified")
        print("[PASS] OPH-019 universal PostgreSQL queue verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom .oad_158_ethereum_finalized_chain_block_acquisition import acquire_ethereum_finalized_chain_observations\nfrom .oad_159_ethereum_fee_transaction_pressure_acquisition import acquire_ethereum_fee_transaction_pressure_observations\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\nPRODUCER="oracle.ethereum_onchain"\nPRIORITY=20\n\ndef _dt(v):\n    if isinstance(v,datetime):\n        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)\n    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))\n    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)\n\ndef canonicalize_ethereum_onchain_observation(x,acquisition_batch_id):\n    raw=RawSourceObservation.create(\n        source_observation_id=x.source_id,\n        observed_at=_dt(x.observed_at),\n        observation_type=x.observation_type,\n        payload={\n            "source_class":x.source_class,\n            "independent_evidence":True,\n            "provider":x.provider,\n            "provider_role":x.provider_role,\n            "chain":x.chain,\n            "network":x.network,\n            "subject":x.subject,\n            "source_url":x.source_url,\n            "provenance_hash":x.provenance_hash,\n            "onchain_payload":dict(x.payload),\n        },\n        provenance={\n            "provider":x.provider,\n            "provider_role":x.provider_role,\n            "source_url":x.source_url,\n            "source_class":x.source_class,\n            "independent_evidence":True,\n            "read_only":True,\n        })\n    return CanonicalObservation.create(\n        source_id="source.onchain.ethereum.mainnet",\n        raw_observation=raw,\n        acquired_at=datetime.now(timezone.utc),\n        acquisition_batch_id=str(acquisition_batch_id))\n\n@dataclass(frozen=True,slots=True)\nclass EthereumPersistenceResult:\n    raw_observations:int\n    canonical_observations:int\n    already_present:int\n    committed_new:int\n    exact_readback:int\n    providers:tuple\n    rows:tuple\n    execution_authority:bool=False\n\ndef persist_current_ethereum_onchain(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):\n    root=Path(root or Path.cwd()).resolve()\n    raw=tuple(acquire_ethereum_finalized_chain_observations(acquisition_timeout_seconds))+tuple(acquire_ethereum_fee_transaction_pressure_observations(acquisition_timeout_seconds))\n    canonical=tuple(canonicalize_ethereum_onchain_observation(x,"oad160.ethereum-onchain") for x in raw)\n    backend=_backend(root); existing=0; missing=[]\n    for i,x in enumerate(canonical):\n        if _query_one(backend,x.observation_id,i) is None: missing.append(x)\n        else: existing+=1\n    committed=0\n    if missing:\n        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)\n        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))\n        accepted=tuple(x for x in events if getattr(x,"accepted",False) is True)\n        if len(accepted)!=len(missing): raise RuntimeError("Ethereum universal single-writer commit mismatch")\n        committed=len(accepted)\n    ids=tuple(x.observation_id for x in canonical)\n    rows=tuple(exact_postgresql_readback(ids,root)) if ids else tuple()\n    if len(rows)!=len(ids): raise RuntimeError("Ethereum exact readback mismatch")\n    providers=tuple(sorted({x.provider for x in raw}))\n    return EthereumPersistenceResult(len(raw),len(canonical),existing,committed,len(rows),providers,rows,False)\n')
        write(test,'import unittest\nfrom unittest.mock import patch\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent import oad_160_ethereum_onchain_canonical_postgresql_persistence as m\nfrom qseries_v2.oracle_adapters.independent.oad_157_ethereum_onchain_evidence_foundation import build_ethereum_onchain_observation\nclass T(unittest.TestCase):\n    def test_persistence_contract(self):\n        o=build_ethereum_onchain_observation(source_id="ethereum:test:1",observation_type="finalized_chain_state",subject="state",observed_at="2026-08-29T00:00:00+00:00",payload={"block_number":1})\n        c=m.canonicalize_ethereum_onchain_observation(o,"test")\n        self.assertEqual(c.source_id,"source.onchain.ethereum.mainnet"); self.assertFalse(c.execution_allowed)\n        with patch.object(m,"acquire_ethereum_finalized_chain_observations",return_value=(o,)),patch.object(m,"acquire_ethereum_fee_transaction_pressure_observations",return_value=()),patch.object(m,"_backend",return_value=object()),patch.object(m,"_query_one",return_value=SimpleNamespace(observation_id=c.observation_id)),patch.object(m,"exact_postgresql_readback",return_value=(SimpleNamespace(observation_id=c.observation_id),)):\n            r=m.persist_current_ethereum_onchain()\n        print("[SOURCE_ID]",c.source_id); print("[PROVIDERS]",r.providers); print("[EXACT_READBACK]",r.exact_readback)\n        self.assertEqual(r.exact_readback,1)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-160 Ethereum on-chain PostgreSQL persistence certified")\n    print("[PASS] producer oracle.ethereum_onchain uses existing OPH-019 universal queue")\n')
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_160_ethereum_onchain_canonical_postgresql_persistence import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-160 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__": main()
