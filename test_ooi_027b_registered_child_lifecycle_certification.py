import importlib
import tempfile
from pathlib import Path
from unittest.mock import patch
from test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,candidate,require,E,FIXED
from test_ooi_019_retained_evidence_snapshot import A
from test_ooi_021_existing_oos_observation_cycle import append_candidate
from test_ooi_022_restart_safe_observation_session import main as certify_restart
from test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock
R=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_026_registered_child_observation')

def main():
    certify_restart()
    with tempfile.TemporaryDirectory() as tmp, fixed_validation_clock(), patch.object(E,'utc_now',return_value=FIXED):
        fixture(tmp);A.retain_snapshot(snapshot(tmp),tmp);append_candidate(tmp,candidate())
        runtime=R.RegisteredChildObservation(tmp)
        root=Path(tmp)
        paths=[root/E.PREDICTIONS,root/E.RESOLUTIONS]
        baseline=[p.read_bytes() for p in paths]
        runtime.prepare('2026-09-17T00:00:20+00:00')
        status=runtime.complete({'unresolved':1},'2026-09-17T00:00:21+00:00')
        require(status['observation']['active_owned_count']==1,'existing OOS lost accepted fixture')
        require(status['observation']['duplicates']==1,'handoff duplicated registered candidate')
        runtime.prepare('2026-09-17T00:01:11+00:00')
        expired=runtime.complete({'unresolved':1},'2026-09-17T00:01:12+00:00')
        require(expired['observation']['active_owned_count']==0,'expired candidate retained')
        require([p.read_bytes() for p in paths]==baseline,'observer modified source ledgers')
        require(runtime.round_count==2,'completed round sequence lost')
    print('[PASS] OOI-027 real session/OOS admission, deduplication, expiry, restart recovery, source immutability')
    print('[SCOPE] Deterministic fixtures; live admission and 24/7 activation remain unclaimed')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__':main()
