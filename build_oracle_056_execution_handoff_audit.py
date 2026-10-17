"""ORACLE-056 full isolated installer: audits ORIGINAL execution handoff without starting a scanner."""
from pathlib import Path
from hashlib import sha256
import os

root = Path.cwd()
pkg = root / 'qseries_v2/oracle_execution/solana_atomic_executor'
original = pkg / 'oracle_054_reverse_native_handoff.py'
monitor = pkg / 'oracle_055_parity_simulation_guard.py'
target = pkg / 'oracle_056_execution_handoff_audit.py'

for required in (original, monitor):
    if not required.is_file():
        raise SystemExit('[HOLD] Required source not found: ' + str(required))

if target.exists() and 'ORACLE056_SOURCE_LOCK' not in target.read_text(
    encoding='utf-8', errors='replace'
):
    raise SystemExit('[HOLD] Unrecognized ORACLE-056 file; refusing replacement')

lock = sha256(original.read_bytes()).hexdigest()

code = r'''from __future__ import annotations
import argparse, ast, hashlib, json, os, re, unittest
from pathlib import Path

ORACLE056_SOURCE_LOCK = '__LOCK__'
ROOT = Path.cwd()
PKG = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor'
PREV = PKG / 'oracle_054_reverse_native_handoff.py'
CHECKPOINT = ROOT / 'runtime_state/oracle/oracle_live_execution/oracle_055_parity_simulation_guard.json'
REPORT = ROOT / 'runtime_state/oracle/oracle_live_execution/oracle_056_execution_handoff_audit.json'
EXECUTION_AUTHORITY = SIGNING = BROADCAST = False

INTEREST = (
    'simulat','native','candidate','admiss','shadow',
    'mriya','replenish','quote','snapshot','price','pump','meteora'
)
SENTINELS = (
    'ORACLE051_SIM','ORACLE054_NATIVE','ORACLE054_SIM',
    'simulateTransaction','sim_attempts','rejected'
)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def classify(check):
    if not isinstance(check,dict):
        return ['HOLD_NO_CHECKPOINT']
    issues=[]
    if int(check.get('simulation_rejection_lines') or 0)>0:
        issues.append('HOLD_REJECTED_ATOMIC_SIMULATIONS')
    if int(check.get('rejected_zero_unit_lines') or 0)>0:
        issues.append('HOLD_ZERO_COMPUTE_REJECTION_CAUSE_UNPROVEN')
    if int(check.get('live_exact_log_rows') or 0)>0 and int(
        check.get('quote_probe_rows') or 0
    )==0:
        issues.append('HOLD_PRICER_MONITOR_NOT_PHYSICALLY_ATTACHED')
    if int(check.get('quote_probe_rows') or 0)>0 and not check.get(
        'quote_state_transition_counts'
    ):
        issues.append('HOLD_INSUFFICIENT_PRICE_PARITY_SAMPLES')
    if check.get('mriya_replenishment_certified') is not True:
        issues.append('HOLD_MRIYA_REPLENISHMENT_NOT_CERTIFIED')
    if check.get('executable_profit_certified') is not True:
        issues.append('HOLD_NO_EXECUTABLE_PROFIT')
    return issues

def scan_file(path):
    code=path.read_text(encoding='utf-8',errors='replace')
    try:
        tree=ast.parse(code,filename=str(path))
    except SyntaxError as exc:
        return {
            'file':str(path.relative_to(ROOT)),
            'parse_error':str(exc.lineno)
        }
    hits=[]
    for node in ast.walk(tree):
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            continue
        literals=[
            x.value for x in ast.walk(node)
            if isinstance(x,ast.Constant) and isinstance(x.value,str)
        ]
        marks=sorted({
            s for s in SENTINELS
            if any(s.lower() in v.lower() for v in literals)
        })
        name=node.name
        if not marks and not any(t in name.lower() for t in INTEREST):
            continue
        calls=[]
        for n in ast.walk(node):
            if not isinstance(n,ast.Call):
                continue
            fn=n.func
            if isinstance(fn,ast.Name):
                c=fn.id
            elif isinstance(fn,ast.Attribute):
                c=(fn.value.id+'.' if isinstance(fn.value,ast.Name) else '')+fn.attr
            else:
                continue
            if any(s in c.lower() for s in INTEREST) or c in (
                'rpc','run','install','compose','submit','send'
            ):
                calls.append(c)
        hits.append({
            'function':name,
            'line':node.lineno,
            'markers':marks,
            'calls':sorted(set(calls))[:14]
        })
    return {
        'file':str(path.relative_to(ROOT)),
        'sha256_prefix':digest(path)[:16],
        'hits':hits[:90],
        'total_hits':len(hits)
    }

def source_paths():
    base=ROOT/'qseries_v2/oracle_execution'
    required=[
        PKG/'oracle_054_reverse_native_handoff.py',
        PKG/'oracle_055_parity_simulation_guard.py'
    ]
    required += [
        base/('oracle_%03d_'%n+stub+'.py')
        for n,stub in (
            (18,'exact_sdk_hot_lane_cutover'),
            (20,'latest_state_exact_pricing_worker'),
            (25,'single_hydration_exact_live_reuse')
        )
    ]
    others=sorted(PKG.glob('oracle_05*.py'))
    imported=[]
    try:
        tree=ast.parse(PREV.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            names=[
                x.name for x in node.names
            ] if isinstance(node,ast.Import) else []
            if isinstance(node,ast.ImportFrom) and node.module:
                names += [node.module]+[
                    node.module+'.'+x.name for x in node.names
                ]
            for name in names:
                if name.startswith('qseries_v2.'):
                    p=ROOT/(name.replace('.','/')+'.py')
                    if p.is_file():
                        imported.append(p)
    except (SyntaxError,OSError):
        pass
    result=[]
    for p in required+others+imported:
        if p.is_file() and p not in result and p.resolve()!=Path(__file__).resolve():
            result.append(p)
    return result

def audit():
    if digest(PREV)!=ORACLE056_SOURCE_LOCK:
        raise RuntimeError('ORACLE054_SOURCE_DRIFT_REFUSE_AUDIT')
    raw={}
    if CHECKPOINT.is_file():
        try:
            raw=json.loads(CHECKPOINT.read_text(encoding='utf-8'))
        except (ValueError,OSError):
            raw={}
    selected=(
        'report_complete','quote_probe_rows',
        'quote_state_transition_counts','live_exact_log_rows',
        'startup_or_unknown_price_rows','startup_max_bps',
        'live_max_bps','simulation_rejection_lines',
        'rejected_zero_unit_lines','mriya_log_lines',
        'mriya_replenishment_certified','executable_profit_certified',
        'oracle_054_source_unchanged'
    )
    state={k:raw.get(k) for k in selected}
    inventory=[scan_file(p) for p in source_paths()]
    report={
        'build':'ORACLE-056',
        'mode':'SOURCE_AND_CHECKPOINT_AUDIT_ONLY',
        'source_lock':ORACLE056_SOURCE_LOCK[:16],
        'sources':inventory,
        'checkpoint':state,
        'holds':classify(raw),
        'scanner_started':False,
        'scanner_modified':False,
        'private_key_accessed':False,
        'signing':False,
        'broadcast':False,
        'profit_certified':False
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    stage=REPORT.with_suffix('.json.tmp')
    stage.write_text(
        json.dumps(report,indent=2,sort_keys=True),
        encoding='utf-8'
    )
    os.replace(stage,REPORT)
    print('[ORACLE056_SOURCE] LOCK_PASS '+ORACLE056_SOURCE_LOCK[:16])
    print(
        '[ORACLE056_CHECKPOINT] quote_rows=%s live_log_rows=%s rejected=%s zero_units=%s' %
        (state['quote_probe_rows'],state['live_exact_log_rows'],
         state['simulation_rejection_lines'],
         state['rejected_zero_unit_lines'])
    )
    print('[ORACLE056_PRICE_TRANSITIONS]',state['quote_state_transition_counts'])
    print('[ORACLE056_SOURCE_COUNT]',len(inventory))
    for x in inventory:
        for h in x.get('hits',[]):
            if h['markers']:
                print(
                    '[ORACLE056_CALLSITE] %s:%s %s markers=%s calls=%s' %
                    (x['file'],h['line'],h['function'],
                     ','.join(h['markers']),','.join(h['calls'][:7]))
                )
    for reason in report['holds']:
        print('[ORACLE056_HOLD]',reason)
    print('[ORACLE056_REPORT]',REPORT)
    print(
        '[EXECUTION] no second scanner; no signing; no broadcasting; '
        'original runtime left running'
    )
    return 0

class Tests(unittest.TestCase):
    def test_source_lock(self):
        self.assertEqual(digest(PREV),ORACLE056_SOURCE_LOCK)
    def test_no_money_permissions(self):
        self.assertFalse(EXECUTION_AUTHORITY or SIGNING or BROADCAST)
    def test_no_checkpoint(self):
        self.assertIn('HOLD_NO_CHECKPOINT',classify(None))
    def test_rejected_simulation(self):
        self.assertIn(
            'HOLD_REJECTED_ATOMIC_SIMULATIONS',
            classify({'simulation_rejection_lines':2})
        )
    def test_parity_probe_missing(self):
        self.assertIn(
            'HOLD_PRICER_MONITOR_NOT_PHYSICALLY_ATTACHED',
            classify({'live_exact_log_rows':2,'quote_probe_rows':0})
        )
    def test_single_scanner_inspection_only(self):
        self.assertTrue(all(x.is_file() for x in source_paths()[:2]))
    def test_known_marker_location(self):
        x=scan_file(PREV)
        self.assertTrue(
            x['file'].endswith('oracle_054_reverse_native_handoff.py')
        )
    def test_positive_unverified(self):
        self.assertIn(
            'HOLD_NO_EXECUTABLE_PROFIT',
            classify({'live_exact_log_rows':20})
        )

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--audit',action='store_true')
    a=p.parse_args(argv)
    if a.test:
        r=unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if r.wasSuccessful() else 1
    if a.audit:
        return audit()
    p.print_help()
    return 0

if __name__=='__main__':
    raise SystemExit(main())
'''.replace('__LOCK__',lock)

target.parent.mkdir(parents=True,exist_ok=True)
compile(code,str(target),'exec')
temp=target.with_suffix('.py.tmp')
temp.write_text(code,encoding='utf-8')
os.replace(temp,target)

print('[PASS] ORACLE-056 installed isolated source + live-checkpoint audit')
print('[SOURCE] ORACLE-054 locked: '+lock[:16])
print('[PRESERVED] Q25/Q20/Q18, Mriya, learning, recovery, native executor')
print('[BOUNDARY] Current original scanner is not restarted, imported or modified')