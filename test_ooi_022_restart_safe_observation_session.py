import importlib
import tempfile
from unittest.mock import patch
from test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,candidate,require,E,FIXED
from test_ooi_019_retained_evidence_snapshot import A
from test_ooi_021_existing_oos_observation_cycle import C,append_candidate
from test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock
R=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_022_restart_safe_observation_session')

def main():
    with tempfile.TemporaryDirectory() as root, fixed_validation_clock(), patch.object(E,'utc_now',return_value=FIXED):
        fixture(root);A.retain_snapshot(snapshot(root),root);append_candidate(root,candidate())
        first=R.OpportunityObservationSession(root,C.OpportunityOperatingSystem())
        a=first.start(evaluated_at='2026-09-17T00:00:20+00:00')
        repeat=first.step(evaluated_at='2026-09-17T00:00:21+00:00')
        require(a['active_owned_count']==1 and repeat['duplicates']==1,'session state not reused')
        recovered=R.OpportunityObservationSession(root,C.OpportunityOperatingSystem())
        b=recovered.start(evaluated_at='2026-09-17T00:00:21+00:00')
        require(b['active_owned_fingerprints']==a['active_owned_fingerprints'],'restart changed active research identity')
        old=R.OpportunityObservationSession(root,C.OpportunityOperatingSystem())
        expired=old.start(evaluated_at='2026-09-17T00:01:11+00:00')
        require(expired['active_owned_count']==0,'restart resurrected expired candidate')
        try:recovered.step(evaluated_at='2026-09-16T23:59:00+00:00')
        except RuntimeError:pass
        else:raise AssertionError('clock rollback ignored')
    print('[PASS] OOI-022 existing OOS session reuse, restart reconstruction, expiry exclusion, clock rollback guard')
    print('[SCOPE] Fixture recovery; production launcher unchanged; execution_authority=FALSE')

if __name__=='__main__':main()
