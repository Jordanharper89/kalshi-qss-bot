"""ORACLE-132 full guarded installer: 0.050 SOL single-size research+atomic preflight.
Windows CMD: python build_oracle_132_0050_sol_unified_test_size.py
Preserves Q25/Q20 fast WS scanner and independent 180-second discovery.
Does NOT authorize signing, broadcast or claims of executable profitability.
"""
from __future__ import annotations
import ast
import os
from pathlib import Path
import py_compile
import shutil
import tempfile

ROOT = Path.cwd()
Q20 = ROOT / 'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'
EXEC = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
PREFLIGHT = ROOT / 'oracle131_native_executor_preflight.py'
REPLENISH = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle129_replenish.py'
TARGET_SIZE = 0.050


def assignments(source):
    found = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    if t.id in ('FAST_SIZES', 'EXPAND_SIZES', 'PREFERRED_SIZE_SOL',
                                'EXECUTION_AUTHORITY', 'PAPER_ONLY'):
                        found[t.id] = (ast.literal_eval(node.value), node)
    return found


def set_exact_size(source, require_preferred):
    values = assignments(source)
    needed = ('FAST_SIZES', 'EXPAND_SIZES') + (('PREFERRED_SIZE_SOL',) if require_preferred else ())
    if any(k not in values for k in needed):
        raise RuntimeError('HOLD_MISSING_SIZE_CONFIGURATION')
    if any(k in values and values[k][0] is not False for k in ('EXECUTION_AUTHORITY',)):
        raise RuntimeError('HOLD_EXECUTION_AUTHORITY_NOT_FALSE')
    if 'PAPER_ONLY' in values and values['PAPER_ONLY'][0] is not True:
        raise RuntimeError('HOLD_PAPER_ONLY_NOT_TRUE')
    old_sizes = values['FAST_SIZES'][0]
    if not isinstance(old_sizes, tuple) or not old_sizes or not all(isinstance(x, (float,int)) for x in old_sizes):
        raise RuntimeError('HOLD_UNEXPECTED_SIZE_CURVE')
    if values['EXPAND_SIZES'][0] != ():
        raise RuntimeError('HOLD_SIZE_EXPANSION_ALREADY_ENABLED')
    if 'PREFERRED_SIZE_SOL' in values and not isinstance(values['PREFERRED_SIZE_SOL'][0], (int, float)):
        raise RuntimeError('HOLD_UNEXPECTED_PREFERRED_SIZE')
    replacement = {'FAST_SIZES':'(0.050,)', 'EXPAND_SIZES':'()', 'PREFERRED_SIZE_SOL':'0.050'}
    lines = source.splitlines(keepends=True)
    for key in sorted(needed, key=lambda k:values[k][1].lineno, reverse=True):
        node = values[key][1]
        lines[node.lineno-1:node.end_lineno] = [key+'='+replacement[key]+'\n']
    out = ''.join(lines)
    check=assignments(out)
    assert check['FAST_SIZES'][0] == (TARGET_SIZE,)
    assert check['EXPAND_SIZES'][0] == ()
    if require_preferred:
        assert check['PREFERRED_SIZE_SOL'][0] == TARGET_SIZE
    return out


def patch_q20(source):
    out=set_exact_size(source, True)
    expected="if abs(row['size_sol'] - 0.010) > 1e-10:"
    changed="if abs(row['size_sol'] - 0.050) > 1e-10:"
    if expected in out:
        if out.count(expected)!=1:raise RuntimeError('HOLD_AMBIGUOUS_HANDOFF_SIZE')
        out=out.replace(expected, changed)
    elif changed not in out:
        raise RuntimeError('HOLD_ORACLE129_POSITIVE_HANDOFF_NOT_FOUND')
    if 'def _o129_offer(' not in out or '_o129_offer(token,snap,slot,received_ns,best)' not in out:
        raise RuntimeError('HOLD_Q20_POSITIVE_HANDOFF_NOT_ACTIVE')
    ast.parse(out)
    return out


def patch_runner(source):
    old_assert="assert found['FAST_SIZES']==(0.010,), 'HOLD_EXECUTOR_CANARY_SIZE'"
    new_assert="assert found['FAST_SIZES']==(0.050,), 'HOLD_EXECUTOR_CANARY_SIZE'"
    if old_assert in source:
        source=source.replace(old_assert,new_assert)
    elif new_assert not in source:
        raise RuntimeError('HOLD_UNKNOWN_PREFLIGHT_VERIFIER')
    old_print="print('[PASS] exact 0.010 SOL; no size expansion; read-only canonical executor')"
    new_print="print('[PASS] exact 0.050 SOL; no size expansion; read-only canonical executor')"
    if old_print in source:source=source.replace(old_print,new_print)
    elif new_print not in source:raise RuntimeError('HOLD_UNKNOWN_PREFLIGHT_BANNER')
    ast.parse(source)
    return source


def ensure_discovery_180(source):
    cadence='time.sleep(max(0,180-(time.monotonic()-start)))'
    if source.count(cadence)!=1 or 'universal_crosslist' not in source:
        raise RuntimeError('HOLD_180_SECOND_DISCOVERY_NOT_INSTALLED')


def validate(q, ex, runner, replenisher):
    qvals=assignments(q); evals=assignments(ex)
    for vals in (qvals, evals):
        assert vals['FAST_SIZES'][0]==(0.050,)
        assert vals['EXPAND_SIZES'][0]==()
        assert vals['EXECUTION_AUTHORITY'][0] is False
    assert qvals['PREFERRED_SIZE_SOL'][0]==0.050
    assert evals['PAPER_ONLY'][0] is True
    assert "if abs(row['size_sol'] - 0.050) > 1e-10:" in q
    assert "assert found['FAST_SIZES']==(0.050,)" in runner
    assert 'ORACLE_EXECUTION_AUTHORITY' in runner
    ensure_discovery_180(replenisher)


def tests():
    q=('EXECUTION_AUTHORITY=False\nPAPER_ONLY=True\nPREFERRED_SIZE_SOL=0.010\n'
       'FAST_SIZES=(0.010,)\nEXPAND_SIZES=()\n'
       'def _o129_offer():\n    pass\n'
       "if abs(row['size_sol'] - 0.010) > 1e-10:\n    return\n"
       '# _o129_offer(token,snap,slot,received_ns,best)\n')
    e='EXECUTION_AUTHORITY=False\nPAPER_ONLY=True\nFAST_SIZES=(0.010,)\nEXPAND_SIZES=()\n'
    r=("assert found['FAST_SIZES']==(0.010,), 'HOLD_EXECUTOR_CANARY_SIZE'\n"
       "print('[PASS] exact 0.010 SOL; no size expansion; read-only canonical executor')\n")
    assert patch_q20(patch_q20(q))==patch_q20(q)
    assert set_exact_size(set_exact_size(e,False),False)==set_exact_size(e,False)
    assert patch_runner(patch_runner(r))==patch_runner(r)
    for unsafe in ('EXECUTION_AUTHORITY=True','PAPER_ONLY=False'):
        try:set_exact_size(e.replace(unsafe.split('=')[0]+'='+('False' if 'AUTHORITY' in unsafe else 'True'),unsafe),False)
        except RuntimeError:pass
        else:raise AssertionError('AUTHORITY_GUARD_NOT_ENFORCED')
    print('[PASS] ORACLE-132 deterministic 0.050 SOL, handoff, preflight, idempotence and authority tests')


def write_atomic(path, source):
    compile(source,str(path),'exec')
    with tempfile.NamedTemporaryFile('w',dir=path.parent,prefix='.oracle132_',suffix='.tmp',encoding='utf-8',delete=False) as f:
        tmp=Path(f.name)
        f.write(source)
    try:os.replace(tmp,path)
    finally:tmp.unlink(missing_ok=True)


def main():
    tests()
    for p in (Q20,EXEC,PREFLIGHT,REPLENISH):
        if not p.is_file():raise SystemExit('[HOLD] Missing prerequisite '+str(p))
    sources={p:p.read_text(encoding='utf-8') for p in (Q20,EXEC,PREFLIGHT)}
    new={Q20:patch_q20(sources[Q20]),
         EXEC:set_exact_size(sources[EXEC],False),
         PREFLIGHT:patch_runner(sources[PREFLIGHT])}
    validate(new[Q20],new[EXEC],new[PREFLIGHT],REPLENISH.read_text(encoding='utf-8'))
    for p in new:
        if new[p]!=sources[p]:
            backup=p.with_suffix(p.suffix+'.oracle132.preinstall.bak')
            if not backup.exists():shutil.copy2(p,backup)
    completed=[]
    try:
        for p,s in new.items():
            if s!=sources[p]:write_atomic(p,s)
            completed.append(p)
        validate(Q20.read_text(encoding='utf-8'),EXEC.read_text(encoding='utf-8'),
                 PREFLIGHT.read_text(encoding='utf-8'),REPLENISH.read_text(encoding='utf-8'))
        for p in new:py_compile.compile(str(p),doraise=True)
    except BaseException:
        for p in completed:write_atomic(p,sources[p])
        raise
    print('[PASS] ORACLE-132 installed and verified')
    print('[Q25_Q20] Original fast WebSocket scanner; 0.050 SOL only; both directions')
    print('[CANDIDATES] Every positive exact 0.050 SOL quote eligible for nonblocking research feed')
    print('[NATIVE_PREFLIGHT] Existing atomic executor search 0.050 SOL only; expansion disabled')
    print('[DISCOVERY] Mriya and pool crosslist independent; 180-second schedule unchanged')
    print('[LEGACY_WARNING] Legacy HOT_SIGNAL_INITIAL path may still evaluate other sizes; NOT EXECUTION CERTIFICATION')
    print('[GUARDS] PAPER_ONLY=True; EXECUTION_AUTHORITY=False; no signing/broadcast')
    print('[VERIFY] python oracle131_native_executor_preflight.py --verify-only')
    print('[RUN] python oracle120_credentials.py --run')

if __name__=='__main__':main()
