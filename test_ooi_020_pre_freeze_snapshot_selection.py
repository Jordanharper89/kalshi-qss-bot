import importlib
import tempfile
from dataclasses import replace
from test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,require,E
from test_ooi_019_retained_evidence_snapshot import A
S=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_020_pre_freeze_snapshot_selection')

def timed(s, when):
    body=dict(captured_at=when,rows_json=s.rows_json,prediction_ledger_hash=s.prediction_ledger_hash,
              resolution_ledger_hash=s.resolution_ledger_hash,execution_authority=False)
    return E.EvidenceSnapshot(snapshot_hash=E.digest(body),**body)

def main():
    with tempfile.TemporaryDirectory() as root:
        fixture(root);early=snapshot(root);late=timed(early,'2026-09-17T00:00:30+00:00')
        A.retain_snapshot(late,root);A.retain_snapshot(early,root)
        saved=S.archived_snapshots(root)
        selected,reason=S.select_pre_freeze_snapshot('2026-09-17T00:00:10+00:00',saved)
        require(selected==early and reason is None,'future snapshot displaced prior evidence')
        selected2,_=S.select_pre_freeze_snapshot('2026-09-17T00:00:10+00:00',S.archived_snapshots(root))
        require(selected2==selected,'restart evidence selection changed')
        none,reason=S.select_pre_freeze_snapshot('2026-09-16T23:59:59+00:00',saved)
        require(none is None and reason=='NO_RETAINED_PRE_FREEZE_SNAPSHOT','future-only archive admitted')
        none,reason=S.select_pre_freeze_snapshot('2026-09-17T02:00:00+00:00',saved)
        require(none is None and reason=='STALE_PRE_FREEZE_SNAPSHOT','stale archive admitted')
        (Path(root)/A.ARCHIVE/'partial.tmp').write_text('partial crash write')
        require(len(S.archived_snapshots(root))==2,'temporary write treated as retained snapshot')
    print('[PASS] OOI-020 pre-freeze selection, restart stability, future/stale HOLD, incomplete-write exclusion')
    print('[PASS] execution_authority=FALSE')

from pathlib import Path
if __name__=='__main__':main()
