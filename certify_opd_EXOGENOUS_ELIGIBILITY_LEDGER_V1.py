from pathlib import Path
import json,subprocess,sys
root=Path.cwd().resolve(); ledger=root/'runtime'/'predictive_data'/'opd_full_evidence_live_prediction_ledger.jsonl'
def load():
    out=[]
    if ledger.exists():
        for line in ledger.read_text(encoding='utf-8').splitlines():
            try: out.append(json.loads(line))
            except Exception: pass
    return out
before=load(); ids={str(x.get('prediction_id')) for x in before if x.get('prediction_id')}
print('[LEDGER BEFORE]',len(before))
code="from pathlib import Path;from qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor import run;run(root=Path.cwd().resolve())"
p=subprocess.run([sys.executable,'-c',code],cwd=str(root),text=True,capture_output=True,timeout=180)
print('[FRESH INTERPRETER EXIT]',p.returncode)
for line in p.stdout.splitlines():
    if 'LIVE_EVIDENCE_EXOGENOUS_SOURCES=' in line or '[PREDICTION LEDGER]' in line or 'LIVE_PREDICTION=' in line:
        print(line)
if p.returncode:
    if p.stderr.strip(): print('[STDERR]',p.stderr[-3000:])
    raise SystemExit('[FAIL] predictor run failed')
after=load(); new=[x for x in after if str(x.get('prediction_id') or '') not in ids]
rows=[x for x in new if isinstance(x.get('exogenous_evidence_snapshot'),dict) and x['exogenous_evidence_snapshot']]
print('[NEW IMMUTABLE ROWS]',len(new)); print('[ROWS WITH NONEMPTY ELIGIBLE SNAPSHOT]',len(rows))
if not rows: raise SystemExit('[FAIL] no eligible snapshot frozen')
bad=[]; sources=set()
for row in rows:
    aseq=int(row['anchor_sequence_boundary']); at=float(row['anchor_observed_epoch'])
    for v in row['exogenous_evidence_snapshot'].values():
        sid=str(v.get('source_id') or ''); typ=str(v.get('observation_type') or ''); low=(sid+' '+typ).lower(); sources.add(sid)
        if int(v['sequence_number'])>aseq: bad.append(('future_seq',sid))
        if v.get('observed_epoch') is not None and float(v['observed_epoch'])>at: bad.append(('future_time',sid))
        if any(z in low for z in ('prospective_forecast','prospective_binding','experience','source.sports','sports.','kalshi','coinbase','polymarket','learned_case')):
            bad.append(('contaminated',sid))
print('[UNIQUE ELIGIBLE SOURCES]',len(sources))
for sid in sorted(sources): print('[ELIGIBLE SOURCE]',sid)
print('[ELIGIBILITY/ANCHOR VIOLATIONS]',len(bad))
if bad:
    for z in bad[:30]: print('[VIOLATION]',z)
    raise SystemExit('[FAIL] contamination/leakage detected')
print('[PASS] clean eligible exogenous evidence physically frozen into new immutable rows')
print('[PASS] internal predictive state and unrelated-domain evidence excluded')
print('[PASS] exact anchor anti-leakage boundary preserved')
print('[RESULT] EXOGENOUS_ELIGIBILITY_PHYSICALLY_CERTIFIED')
print('[EXECUTION/PUBLICATION] FALSE/FALSE')
