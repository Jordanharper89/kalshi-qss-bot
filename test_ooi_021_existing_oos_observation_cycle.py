import importlib
import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,candidate,require,E
from test_ooi_019_retained_evidence_snapshot import A
from test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock
C=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_021_existing_oos_observation_cycle')

def append_candidate(root, op):
    p=Path(root)/E.PREDICTIONS
    doc=json.loads(p.read_text());doc['predictions'].append(asdict(op));p.write_text(json.dumps(doc))

def main():
    with tempfile.TemporaryDirectory() as root, fixed_validation_clock():
        fixture(root);A.retain_snapshot(snapshot(root),root);op=candidate();append_candidate(root,op)
        oos=C.OpportunityOperatingSystem()
        first=C.observation_cycle(root,oos,evaluated_at='2026-09-17T00:00:20+00:00')
        require(first['accepted']==first['registered']==first['active_owned_count']==1,'live-source fixture not admitted')
        repeat=C.observation_cycle(root,oos,evaluated_at='2026-09-17T00:00:20+00:00')
        require(repeat['duplicates']==1 and repeat['active_owned_count']==1,'duplicate registry entry')
        fingerprints=repeat['active_owned_fingerprints']
        expired=C.observation_cycle(root,oos,evaluated_at='2026-09-17T00:01:10+00:00')
        require(expired['active_owned_count']==0 and len(expired['removed'])==1,'expired record remained')
        fresh_oos=C.OpportunityOperatingSystem()
        C.observation_cycle(root,fresh_oos,evaluated_at='2026-09-17T00:00:20+00:00')
        p=Path(root)/E.RESOLUTIONS;doc=json.loads(p.read_text())
        doc['resolutions'].append(dict(prediction_id=op.prediction_id,outcome='TARGET_FIRST',gross_return=.10,net_return=.08,
            terminal_return=.10,mfe=.10,mae=0,friction_bps=200,execution_authority=False));p.write_text(json.dumps(doc))
        resolved=C.observation_cycle(root,fresh_oos,evaluated_at='2026-09-17T00:00:30+00:00')
        require(resolved['active_owned_count']==0 and resolved['fresh_candidates']==0,'resolved candidate remained active')
    with tempfile.TemporaryDirectory() as root, fixed_validation_clock():
        fixture(root);append_candidate(root,candidate());oos=C.OpportunityOperatingSystem()
        report=C.observation_cycle(root,oos,evaluated_at='2026-09-17T00:00:20+00:00')
        require(report['held']==1 and report['active_owned_count']==0,'missing snapshot silently bypassed')
    print('[PASS] OOI-021 native prediction ledger -> existing OOS; deduplication, expiry, resolution removal, HOLD')
    print('[SCOPE] Deterministic temporary-source fixture; execution_authority=FALSE')

if __name__=='__main__':main()
