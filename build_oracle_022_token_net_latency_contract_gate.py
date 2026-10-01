from pathlib import Path
import py_compile, textwrap

ROOT=Path.cwd()
SUB=ROOT/'qseries_v2'/'oracle_execution'
SUB.mkdir(parents=True,exist_ok=True)

MOD=SUB/'oracle_022_token_net_latency_contract_gate.py'
TEST=ROOT/'test_oracle_022_token_net_latency_contract_gate.py'
RUN=ROOT/'run_oracle_022_token_net_latency_contract_gate.py'

module_src=r'''
from __future__ import annotations
import argparse,inspect,json,statistics,time
from pathlib import Path
from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
GROSS_VALUES=(1_000,10_000,100_000,1_000_000)

def pct(xs,p):
    if not xs:return None
    s=sorted(xs)
    return s[min(len(s)-1,int(len(s)*p))]

def first_pair(root):
    state=q19.persistent.m.prepare(Path(root))
    pairs=list(state.get('pairs') or [])
    if not pairs: raise RuntimeError('NO_LIVE_PAIR_STATE')
    return pairs[0]

def run(iterations=2):
    pair=first_pair(Path.cwd())
    fn=q18.q14.engine.net_received
    try:
        source=inspect.getsource(fn)
    except Exception as exc:
        source='SOURCE_UNAVAILABLE:%s:%s'%(type(exc).__name__,str(exc))

    rows=[]
    print('[ORACLE-022] TOKEN NET LATENCY + CONTRACT GATE',flush=True)
    print('[TOKEN] %s'%pair.token,flush=True)
    print('[FUNCTION] %s.%s'%(fn.__module__,fn.__name__),flush=True)
    print('[PRIVATE_KEY] not required',flush=True)
    print('[BROADCAST] disabled',flush=True)

    for gross in GROSS_VALUES:
        for i in range(int(iterations)):
            t=time.perf_counter_ns()
            out=fn(pair.token,int(gross))
            elapsed=(time.perf_counter_ns()-t)/1e6
            net=int(out['net'])
            keys=sorted(str(k) for k in out.keys())
            rows.append({'gross':int(gross),'net':net,'iteration':i+1,'elapsed_ms':elapsed,'keys':keys})
            print('[ORACLE022_POINT] gross=%d net=%d i=%d elapsed_ms=%.3f keys=%s'%(
                gross,net,i+1,elapsed,','.join(keys)),flush=True)

    vals=[r['elapsed_ms'] for r in rows]
    summary={'p50_ms':statistics.median(vals),'p95_ms':pct(vals,.95),'max_ms':max(vals),'calls':len(vals)}
    payload={
        'oracle_build':'ORACLE-022','token':pair.token,'function_module':fn.__module__,
        'function_name':fn.__name__,'source':source,'rows':rows,'summary':summary,
        'execution_authority':False,'paper_only':True,'real_money_moved':False,'broadcast':False,
    }
    out=Path('runtime_state/oracle/oracle_live_execution/oracle_022_token_net_latency_contract_gate.json')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding='utf-8')
    srcout=Path('ORACLE_022_NET_RECEIVED_SOURCE.txt')
    srcout.write_text(source,encoding='utf-8')

    print('[ORACLE022_SUMMARY] '+json.dumps(summary,sort_keys=True),flush=True)
    print('[SOURCE_REPORT] %s'%srcout,flush=True)
    print('[REPORT] %s'%out,flush=True)
    print('[BROADCAST] disabled',flush=True)
    return 0

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--iterations',type=int,default=2)
    a=ap.parse_args(argv)
    return run(a.iterations)

if __name__=='__main__':
    raise SystemExit(main())
'''

test_src=r'''
import inspect,unittest
from qseries_v2.oracle_execution import oracle_022_token_net_latency_contract_gate as q22

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q22.EXECUTION_AUTHORITY)
        self.assertTrue(q22.PAPER_ONLY)
        self.assertFalse(q22.REAL_MONEY_MOVED)
    def test_exact_net_received_target(self):
        s=inspect.getsource(q22.run)
        self.assertIn('q18.q14.engine.net_received',s)
    def test_multiple_amounts(self):
        self.assertEqual(q22.GROSS_VALUES,(1000,10000,100000,1000000))
    def test_no_private_key_or_broadcast(self):
        s=inspect.getsource(q22)
        self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',s)
        self.assertNotIn('sendTransaction',s)

if __name__=='__main__':
    unittest.main(verbosity=2)
'''

run_src=r'''
from qseries_v2.oracle_execution.oracle_022_token_net_latency_contract_gate import main
if __name__=='__main__':
    raise SystemExit(main())
'''

MOD.write_text(textwrap.dedent(module_src).lstrip(),encoding='utf-8')
TEST.write_text(textwrap.dedent(test_src).lstrip(),encoding='utf-8')
RUN.write_text(textwrap.dedent(run_src).lstrip(),encoding='utf-8')
for f in (MOD,TEST,RUN):
    py_compile.compile(str(f),doraise=True)

print('[PASS] ORACLE-022 token net latency + contract gate installed')
print('[TARGET] exact q14.engine.net_received implementation')
print('[MEASURE] 8 physical calls across multiple gross amounts')
print('[CAPTURE] installed source written to ORACLE_022_NET_RECEIVED_SOURCE.txt')
print('[PRIVATE_KEY] not required')
print('[BROADCAST] disabled')
print('[OWNER] ORACLE')
