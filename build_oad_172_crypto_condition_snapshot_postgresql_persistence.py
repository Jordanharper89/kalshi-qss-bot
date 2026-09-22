from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_172_CRYPTO_CONDITION_SNAPSHOT_POSTGRESQL_PERSISTENCE_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (\n    RawSourceObservation,CanonicalObservation,\n)\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (\n    submit_observation_batch,await_request,\n)\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom .oad_168_crypto_condition_state_normalization import CryptoConditionState\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\nPRODUCER="oracle.crypto_condition_history"\nPRIORITY=20\nSOURCE_PREFIX="source.crypto.condition."\n\n@dataclass(frozen=True,slots=True)\nclass CryptoConditionSnapshotPersistenceResult:\n    snapshot_at:str\n    condition_states:int\n    canonical_observations:int\n    already_present:int\n    committed_new:int\n    exact_readback:int\n    observation_ids:tuple\n    execution_authority:bool=False\n\ndef _dt(v):\n    if isinstance(v,datetime):\n        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)\n    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))\n    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)\n\ndef stamp_crypto_condition_states(states,snapshot_at):\n    stamp=_dt(snapshot_at).astimezone(timezone.utc).isoformat()\n    out=[]\n    for x in tuple(states):\n        out.append(CryptoConditionState(\n            asset=str(x.asset),\n            source_family=str(x.source_family),\n            metric_name=str(x.metric_name),\n            value=float(x.value),\n            unit=str(x.unit),\n            condition=str(x.condition),\n            basis=str(x.basis),\n            independent_evidence=bool(x.independent_evidence),\n            market_native_reference=bool(x.market_native_reference),\n            observed_at=stamp,\n        ))\n    return tuple(out)\n\ndef canonicalize_crypto_condition_state(x,acquisition_batch_id,snapshot_at,evidence_observed_at=None):\n    stamp=_dt(snapshot_at)\n    metric_token=str(x.metric_name).replace(" ","_").lower()\n    family_token=str(x.source_family).replace(" ","_").lower()\n    asset=str(x.asset).upper()\n    source_id=f"{SOURCE_PREFIX}{asset.lower()}.{family_token}.{metric_token}"\n    raw=RawSourceObservation.create(\n        source_observation_id=f"crypto-condition:{asset}:{family_token}:{metric_token}:{stamp.isoformat()}",\n        observed_at=stamp,\n        observation_type="crypto_condition_snapshot",\n        payload={\n            "asset":asset,\n            "source_family":str(x.source_family),\n            "metric_name":str(x.metric_name),\n            "value":float(x.value),\n            "unit":str(x.unit),\n            "condition":str(x.condition),\n            "basis":str(x.basis),\n            "independent_evidence":bool(x.independent_evidence),\n            "market_native_reference":bool(x.market_native_reference),\n            "evidence_observed_at":None if evidence_observed_at is None else str(evidence_observed_at),\n            "snapshot_at":stamp.isoformat(),\n            "direction":None,\n            "probability":None,\n        },\n        provenance={\n            "producer":PRODUCER,\n            "source_family":str(x.source_family),\n            "independent_evidence":bool(x.independent_evidence),\n            "market_native_reference":bool(x.market_native_reference),\n            "read_only":True,\n        },\n    )\n    return CanonicalObservation.create(\n        source_id=source_id,\n        raw_observation=raw,\n        acquired_at=datetime.now(timezone.utc),\n        acquisition_batch_id=str(acquisition_batch_id),\n    )\n\ndef persist_crypto_condition_snapshot(states,root=None,timeout_seconds=120.0,snapshot_at=None,evidence_observed_at_by_key=None):\n    root=Path(root or Path.cwd()).resolve()\n    stamp=_dt(snapshot_at or datetime.now(timezone.utc))\n    stamped=stamp_crypto_condition_states(states,stamp)\n    evidence_observed_at_by_key=dict(evidence_observed_at_by_key or {})\n    canonical=tuple(\n        canonicalize_crypto_condition_state(\n            x,"oad172.crypto-condition-history",stamp,\n            evidence_observed_at_by_key.get((x.asset,x.source_family,x.metric_name)),\n        )\n        for x in stamped\n    )\n    backend=_backend(root)\n    existing=0\n    missing=[]\n    for i,x in enumerate(canonical):\n        if _query_one(backend,x.observation_id,i) is None:\n            missing.append(x)\n        else:\n            existing+=1\n    committed=0\n    if missing:\n        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)\n        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))\n        accepted=tuple(x for x in events if getattr(x,"accepted",False) is True)\n        if len(accepted)!=len(missing):\n            raise RuntimeError("crypto condition snapshot single-writer commit mismatch")\n        committed=len(accepted)\n    ids=tuple(x.observation_id for x in canonical)\n    rows=tuple(exact_postgresql_readback(ids,root)) if ids else tuple()\n    if len(rows)!=len(ids):\n        raise RuntimeError("crypto condition snapshot exact readback mismatch")\n    return CryptoConditionSnapshotPersistenceResult(\n        stamp.isoformat(),len(stamped),len(canonical),existing,committed,len(rows),ids,False\n    )\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_adapters.independent.oad_172_crypto_condition_snapshot_postgresql_persistence import (\n    canonicalize_crypto_condition_state,stamp_crypto_condition_states\n)\nclass T(unittest.TestCase):\n    def test_snapshot_contract(self):\n        s=SimpleNamespace(\n            asset="BTC",source_family="bitcoin",metric_name="fastest_fee_rate",\n            value=12.0,unit="sat/vB",condition="ELEVATED",basis="10<=sat_vb<50",\n            independent_evidence=True,market_native_reference=False,\n            observed_at="2026-08-29T00:00:00+00:00"\n        )\n        stamp=datetime(2026,8,29,1,0,0,tzinfo=timezone.utc)\n        stamped=stamp_crypto_condition_states((s,),stamp)[0]\n        c=canonicalize_crypto_condition_state(stamped,"test",stamp,s.observed_at)\n        p=dict(c.payload)\n        print("[SOURCE_ID]",c.source_id)\n        print("[SNAPSHOT_AT]",p["snapshot_at"])\n        print("[EVIDENCE_AT]",p["evidence_observed_at"])\n        self.assertTrue(c.source_id.startswith("source.crypto.condition.btc.bitcoin."))\n        self.assertEqual(c.observed_at,stamp)\n        self.assertEqual(p["evidence_observed_at"],s.observed_at)\n        self.assertTrue(c.read_only)\n        self.assertFalse(c.execution_allowed)\n        self.assertIsNone(p["direction"])\n        self.assertIsNone(p["probability"])\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-172 durable crypto condition snapshot contract certified")\n'

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
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_172_crypto_condition_snapshot_postgresql_persistence.py'; test=r/'test_oad_172_crypto_condition_snapshot_postgresql_persistence.py'; init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-172 CRYPTO CONDITION SNAPSHOT POSTGRESQL PERSISTENCE INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_068_exact_postgresql_independent_readback.py', 'oad_168_crypto_condition_state_normalization.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_172_crypto_condition_snapshot_postgresql_persistence import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-172 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__": main()
