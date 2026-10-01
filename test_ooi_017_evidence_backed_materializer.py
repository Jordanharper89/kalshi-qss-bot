import importlib
import tempfile
from test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,candidate,require
M=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_006_slop_universal_opportunity_materializer')

def main():
    with tempfile.TemporaryDirectory() as root:
        fixture(root);snap=snapshot(root);op=candidate()
        legacy=M.materialize_slop(op)
        require(legacy.confidence==legacy.expected_edge==0,'legacy no-evidence behavior changed')
        a=M.materialize_slop(op,snap,evaluated_at=op.frozen_at)
        b=M.materialize_slop(op,snap,evaluated_at=op.frozen_at)
        require(a.to_dict()==b.to_dict() and a.fingerprint()==b.fingerprint(),'materialization not deterministic')
        require(a.metadata['evidence_admission_eligible'] and abs(a.expected_edge-.055)<1e-12,'evidence mapping failed')
        require(len(a.evidence_refs)==24 and len(a.supporting_prediction_ids)==25,'evidence lineage lost')
        require(a.metadata['stop']==.05 and a.metadata['friction_bps']==200,'native frozen thesis changed')
        require(a.execution.required_execution_adapter=='solana_wallet' and a.read_only,'adapter/authority contract failed')
        require(a.metadata['execution_authority'] is False and a.metadata['execution_adapter_invoked'] is False,'authority changed')
        expired=M.materialize_slop(op,snap,evaluated_at='2026-09-17T00:01:10+00:00')
        require(not expired.metadata['evidence_admission_eligible'] and expired.confidence==expired.expected_edge==0,'expiry gate failed')
        future=M.materialize_slop(candidate(frozen_at='2026-09-16T23:59:59+00:00'),snap,evaluated_at='2026-09-17T00:00:00+00:00')
        require(not future.metadata['evidence_admission_eligible'],'future-data gate failed')
    print('[PASS] OOI-017 existing materializer: supported historical edge/confidence, complete lineage, expiry/HOLD')
    print('[SCOPE] Historical research estimate, not calibrated forecast; execution_authority=FALSE')

if __name__=='__main__':main()
