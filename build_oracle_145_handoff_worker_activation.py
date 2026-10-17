"""ORACLE-145 complete installer: activate existing Q20->144 native probe worker.
Does not modify the scanner's pricing, credentials, RPC, or execution authority.
"""
from pathlib import Path
import ast
import os
import subprocess
import sys
import tempfile

ROOT = Path.cwd()
FAST = ROOT / 'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'
PKG = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker'
MOD = PKG / 'oracle144_native_route_handoff.py'
CHECK = PKG / 'oracle145_handoff_activation_test.py'
TEST_SOURCE = r'''"""Offline activation test; no RPC, private keys, or real trades."""
import ast
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
from qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker import oracle144_native_route_handoff as h


def test():
    src=Path('qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py').read_text(encoding='utf8')
    ast.parse(src)
    assert src.count('_o144.start()') == 1, 'ORACLE144_WORKER_START_MISSING'
    assert src.count('_o144.offer(token,snap,slot,received_ns,best)') == 1, 'ORACLE144_OFFER_MISSING'
    assert '_o143.start()' not in src, 'LEGACY_143_WORKER_STILL_ACTIVE'
    assert '_o143.offer(token,snap,slot,received_ns,best)' not in src, 'LEGACY_143_OFFER_STILL_ACTIVE'
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'handoff.jsonl'
        with patch.object(h,'OUT',out), patch.object(h,'probe_native',return_value=('HOLD_NATIVE_TEMPLATE_NOT_INITIALIZED',None)):
            h.start()
            snap={'token':'OFFLINE_FIXTURE','pump_pool':'OFFLINE_POOL','meteora':{'address':'OFFLINE_DLMM'}}
            quote={'size_sol':.05,'local_net':150000,'local_bps':30.,'direction':'PUMP_TO_METEORA'}
            assert h.offer('OFFLINE_FIXTURE',snap,77,time.perf_counter_ns(),quote)=='READY_FOR_NATIVE_ROUTE_PROBE'
            h.Q.join()
            rows=[json.loads(x) for x in out.read_text(encoding='utf8').splitlines()]
            assert len(rows)==1 and rows[0]['slot']==77, 'NATIVE_ROUTE_REPORT_MISSING'
            assert rows[0]['decision'] in {'HOLD_NATIVE_TEMPLATE_NOT_INITIALIZED', 'HOLD_NATIVE_ROUTE_API_MISSING'}, rows[0]
            assert rows[0]['signed'] is False and rows[0]['simulated'] is False and rows[0]['broadcast'] is False
    print('[TEST PASS] ORACLE145 Q20->144 hook active; offline positive delivered; native holds; no signing/broadcast')

if __name__=='__main__':test()
'''


def replace_atomic(path, data):
    with tempfile.NamedTemporaryFile('wb', dir=path.parent, delete=False) as f:
        f.write(data)
        t=Path(f.name)
    os.replace(t,path)


def main():
    if not FAST.exists() or not MOD.exists():
        raise SystemExit('[HOLD] ORACLE144 installation missing; repository untouched')
    source=FAST.read_text(encoding='utf8')
    module=MOD.read_text(encoding='utf8')
    ast.parse(source); ast.parse(module); ast.parse(TEST_SOURCE)
    offer='_o144.offer(token,snap,slot,received_ns,best)'
    start='_o144.start()'
    if source.count(offer)!=1:
        raise SystemExit('[HOLD] ORACLE144 offer hook missing or ambiguous; no changes')
    if 'def probe_native(' not in module or 'def start(' not in module:
        raise SystemExit('[HOLD] ORACLE144 native worker API unrecognized')
    if source.count('_o143.start()')==1 and source.count(start)==0:
        updated=source.replace('_o143.start()',start,1)
    elif source.count(start)==1 and '_o143.start()' not in source:
        updated=source
    else:
        raise SystemExit('[HOLD] Q20 startup seam ambiguous; no changes')
    if updated.count(start)!=1 or updated.count(offer)!=1:
        raise SystemExit('[HOLD] Hook identity verification failed')
    ast.parse(updated)
    original=FAST.read_bytes()
    previous=CHECK.read_bytes() if CHECK.exists() else None
    try:
        replace_atomic(FAST,updated.encode('utf8'))
        replace_atomic(CHECK,TEST_SOURCE.encode('utf8'))
        r=subprocess.run([sys.executable,'-m',
            'qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker.oracle145_handoff_activation_test'],
            cwd=ROOT,text=True,capture_output=True,timeout=25)
        if r.returncode:
            raise RuntimeError((r.stdout+r.stderr)[-2500:])
        print(r.stdout.strip())
    except BaseException as ex:
        replace_atomic(FAST,original)
        if previous is None:CHECK.unlink(missing_ok=True)
        else:replace_atomic(CHECK,previous)
        raise SystemExit('[HOLD] ORACLE145 rollback: '+str(ex))
    print('[INSTALL PASS] ORACLE145 native preflight worker activated; existing scanner untouched otherwise')
    print('[RUN] python oracle120_credentials.py --run')

if __name__=='__main__':main()
