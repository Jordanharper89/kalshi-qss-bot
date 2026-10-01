import importlib
import tempfile
from test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,candidate,require
from test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock
B=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_007b_slop_existing_oos_intake')
G=importlib.import_module('qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_subsystem_integration_gate')

def main():
    with tempfile.TemporaryDirectory() as root, fixed_validation_clock():
        fixture(root);snap=snapshot(root);op=candidate()
        oos=B.OpportunityOperatingSystem()
        result=B.process_evidence_backed_slop([op],snap,oos,evaluated_at=op.frozen_at)
        pipe=result['pipeline']
        require(result['accepted_count']==1 and len(oos.all_records())==1,'nonempty registry handoff failed')
        require(pipe.input_count==pipe.registered_count==pipe.ranked_count==1,'nonempty pipeline counts failed')
        require(all(r.is_accepted() for r in result['validation_reports']),'default validator rejected positive fixture')
        replay=B.process_evidence_backed_slop([op],snap,oos,evaluated_at=op.frozen_at)
        require(replay['pipeline'].duplicate_count==1 and len(oos.all_records())==1,'nonempty duplicate handling failed')
        opportunity=oos.all_records()[0].opportunity
        gate=G.run_opportunity_subsystem_integration_gate(opportunities=[opportunity],observed_at=op.frozen_at,source=B.SOURCE)
        require(gate.passed is True and gate.fail_count==0 and gate.verify_integration_hash(),'nonempty existing integration gate failed')
        require(gate.read_only is True and gate.execution_allowed is False,'integration authority failure')
        G.assert_opportunity_subsystem_read_only(gate)
        held_oos=B.OpportunityOperatingSystem()
        held=B.process_evidence_backed_slop([op],snap,held_oos,evaluated_at='2026-09-17T00:01:10+00:00')
        require(held['accepted_count']==0 and len(held_oos.all_records())==0,'expired candidate registered')
        fixture(root,count=2)
        insufficient=B.process_evidence_backed_slop([op],snapshot(root),held_oos,evaluated_at=op.frozen_at)
        require(insufficient['accepted_count']==0 and len(held_oos.all_records())==0,'insufficient cohort registered')
    print('[PASS] OOI-018 NONEMPTY fixture: accepted=1 registered=1 ranked=1; replay duplicate=1')
    print('[PASS] Actual OOS validation/ranking/integration gate; expiry and evidence HOLD exclusions')
    print('[SCOPE] Deterministic fixture certification, NOT live admission or runtime activation')
    print('[PASS] Oracle read_only=True execution_authority=FALSE; Q Series sole execution authority')

if __name__=='__main__':main()
