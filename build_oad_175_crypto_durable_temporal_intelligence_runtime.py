from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_175_CRYPTO_DURABLE_TEMPORAL_INTELLIGENCE_RUNTIME_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_163_crypto_live_multi_source_cohort import build_crypto_live_multi_source_cohort\nfrom .oad_167_crypto_structured_condition_metric_extraction import extract_crypto_condition_metrics\nfrom .oad_168_crypto_condition_state_normalization import normalize_crypto_condition_states\nfrom .oad_169_crypto_temporal_condition_change_evaluator import evaluate_crypto_temporal_condition_changes\nfrom .oad_170_crypto_cross_source_consistency_profile import build_crypto_cross_source_consistency_profiles\nfrom .oad_172_crypto_condition_snapshot_postgresql_persistence import (\n    stamp_crypto_condition_states,persist_crypto_condition_snapshot,\n)\nfrom .oad_173_crypto_condition_recent_history_exact_readback import read_recent_crypto_condition_history\nfrom .oad_174_crypto_historical_condition_sequence_and_prior_state import (\n    select_latest_prior_comparable_states,build_crypto_condition_sequences,\n)\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoDurableTemporalIntelligenceResult:\n    snapshot_at:str\n    cohort_state:str\n    current_states:int\n    historical_states:int\n    exact_prior_states:int\n    comparable_temporal_metrics:int\n    increased:int\n    decreased:int\n    unchanged:int\n    no_comparable_history:int\n    sequences:int\n    cross_source_assets:tuple\n    committed_new:int\n    exact_readback:int\n    changes:tuple\n    profiles:tuple\n    runtime_ready:bool\n    execution_authority:bool=False\n\ndef run_crypto_durable_temporal_intelligence(\n    root=None,\n    timeout_seconds=120.0,\n    acquisition_timeout_seconds=20.0,\n    lookback_seconds=21600.0,\n    history_limit=10000,\n    snapshot_at=None,\n):\n    stamp=snapshot_at or datetime.now(timezone.utc)\n    if stamp.tzinfo is None: stamp=stamp.replace(tzinfo=timezone.utc)\n    stamp=stamp.astimezone(timezone.utc)\n\n    history=read_recent_crypto_condition_history(\n        root=root,lookback_seconds=lookback_seconds,limit=history_limit,now=stamp\n    )\n\n    cohort=build_crypto_live_multi_source_cohort(acquisition_timeout_seconds)\n    metrics=extract_crypto_condition_metrics(cohort)\n    raw_states=normalize_crypto_condition_states(metrics)\n    evidence_times={(x.asset,x.source_family,x.metric_name):x.observed_at for x in raw_states}\n    current=stamp_crypto_condition_states(raw_states,stamp)\n\n    prior=select_latest_prior_comparable_states(current,history.states)\n    changes=evaluate_crypto_temporal_condition_changes(current,prior)\n    profiles=build_crypto_cross_source_consistency_profiles(current,changes)\n    sequences=build_crypto_condition_sequences(history.states)\n\n    persisted=persist_crypto_condition_snapshot(\n        current,root=root,timeout_seconds=timeout_seconds,snapshot_at=stamp,\n        evidence_observed_at_by_key=evidence_times,\n    )\n\n    cross=tuple(x.asset for x in profiles if x.evidence_state=="CROSS_SOURCE_PRESENT")\n    comparable=sum(1 for x in changes if x.comparable_history_present)\n    inc=sum(1 for x in changes if x.temporal_state=="INCREASED")\n    dec=sum(1 for x in changes if x.temporal_state=="DECREASED")\n    same=sum(1 for x in changes if x.temporal_state=="UNCHANGED")\n    none=sum(1 for x in changes if x.temporal_state=="NO_COMPARABLE_HISTORY")\n    ready=bool(current and cross and persisted.exact_readback==len(current))\n\n    return CryptoDurableTemporalIntelligenceResult(\n        stamp.isoformat(),cohort.state,len(current),len(history.states),len(prior),\n        comparable,inc,dec,same,none,len(sequences),cross,\n        persisted.committed_new,persisted.exact_readback,changes,profiles,ready,False\n    )\n'
TEST_SOURCE='import unittest\nfrom datetime import datetime,timezone\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_175_crypto_durable_temporal_intelligence_runtime as m\n\ndef state(t,v):\n    return SimpleNamespace(\n        asset="BTC",source_family="bitcoin",metric_name="fastest_fee_rate",\n        value=v,unit="sat/vB",condition="OBSERVED",basis="raw",\n        independent_evidence=True,market_native_reference=False,observed_at=t\n    )\nclass T(unittest.TestCase):\n    def test_durable_compare_order(self):\n        stamp=datetime(2026,8,29,2,0,0,tzinfo=timezone.utc)\n        hist=state("2026-08-29T01:00:00+00:00",10)\n        cur=state("2026-08-29T02:00:00+00:00",12)\n        order=[]\n        fake_hist=SimpleNamespace(states=(hist,))\n        fake_cohort=SimpleNamespace(state="FULL_COVERAGE")\n        fake_persist=SimpleNamespace(committed_new=1,exact_readback=1)\n        fake_profile=SimpleNamespace(asset="BTC",evidence_state="CROSS_SOURCE_PRESENT")\n        with patch.object(m,"read_recent_crypto_condition_history",side_effect=lambda **k:(order.append("read") or fake_hist)), \\\n             patch.object(m,"build_crypto_live_multi_source_cohort",return_value=fake_cohort), \\\n             patch.object(m,"extract_crypto_condition_metrics",return_value=(1,)), \\\n             patch.object(m,"normalize_crypto_condition_states",return_value=(cur,)), \\\n             patch.object(m,"stamp_crypto_condition_states",return_value=(cur,)), \\\n             patch.object(m,"build_crypto_cross_source_consistency_profiles",return_value=(fake_profile,)), \\\n             patch.object(m,"persist_crypto_condition_snapshot",side_effect=lambda *a,**k:(order.append("persist") or fake_persist)):\n            r=m.run_crypto_durable_temporal_intelligence(snapshot_at=stamp)\n        print("[ORDER]",order)\n        print("[COMPARABLE]",r.comparable_temporal_metrics)\n        self.assertEqual(order,["read","persist"])\n        self.assertEqual(r.comparable_temporal_metrics,1)\n        self.assertEqual(r.increased,1)\n        self.assertTrue(r.runtime_ready)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-175 read-prior-then-persist temporal runtime certified")\n'

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
    module=pkg/'oad_175_crypto_durable_temporal_intelligence_runtime.py'; test=r/'test_oad_175_crypto_durable_temporal_intelligence_runtime.py'; init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-175 CRYPTO DURABLE TEMPORAL INTELLIGENCE RUNTIME INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_163_crypto_live_multi_source_cohort.py', 'oad_167_crypto_structured_condition_metric_extraction.py', 'oad_168_crypto_condition_state_normalization.py', 'oad_169_crypto_temporal_condition_change_evaluator.py', 'oad_170_crypto_cross_source_consistency_profile.py', 'oad_172_crypto_condition_snapshot_postgresql_persistence.py', 'oad_173_crypto_condition_recent_history_exact_readback.py', 'oad_174_crypto_historical_condition_sequence_and_prior_state.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_175_crypto_durable_temporal_intelligence_runtime import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-175 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__": main()
