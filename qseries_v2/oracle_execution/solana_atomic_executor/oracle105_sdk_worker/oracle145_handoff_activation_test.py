"""Offline activation test; no RPC, private keys, or real trades."""
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
