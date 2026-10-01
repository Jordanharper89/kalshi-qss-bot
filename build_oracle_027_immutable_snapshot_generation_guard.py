from pathlib import Path
import py_compile, textwrap

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2"/"oracle_execution"
SUB.mkdir(parents=True,exist_ok=True)

MOD=SUB/"oracle_027_immutable_snapshot_generation_guard.py"
TEST=ROOT/"test_oracle_027_immutable_snapshot_generation_guard.py"
RUN=ROOT/"run_oracle_027_immutable_snapshot_generation_guard.py"

module_src=r"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from meteora_dlmm import PoolState

from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23
from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

def frozen_pair_snapshot(pair):
    arrays=tuple((a[0],a[1],bytes(a[2])) for a in list(pair.arrays))
    return {
        "token":str(pair.token),
        "pump_pool":str(pair.pump_pool),
        "meteora":{
            "address":str(pair.meteora_pool),
            "token_x":str(pair.token_x),
            "token_y":str(pair.token_y),
            "decimals_x":int(pair.decimals_x),
            "decimals_y":int(pair.decimals_y),
        },
        "lb_bytes":bytes(pair.lb_bytes),
        "arrays_raw":arrays,
        "pump_base_reserve":int(pair.pump_base_reserve),
        "pump_quote_reserve":int(pair.pump_quote_reserve),
        "source_slot":int(getattr(pair,"last_slot",0) or 0),
        "source_event_ns":int(getattr(pair,"last_event_ns",0) or 0),
    }

def materialize_snapshot(snap):
    meta=snap["meteora"]
    state=PoolState.from_accounts(
        snap["lb_bytes"],
        [x[2] for x in snap["arrays_raw"]],
        decimals_x=int(meta["decimals_x"]),
        decimals_y=int(meta["decimals_y"]),
        lb_pair_key=q18.core.b58d(meta["address"]),
        exhaustive=True,
    )
    out=dict(snap)
    out["dlmm_state"]=state
    return out

class ImmutableLatestStateLane(q20.LatestStateLane):
    def __init__(self):
        super().__init__()
        self.latest_generation={}
        self.end_generation_drops=0
        self.materialize_ms=[]

    def submit(self,token,snap,slot,received_ns):
        with self.cv:
            self.submitted+=1
            generation=self.submitted
            self.latest_generation[token]=generation
            if token in self.latest:
                self.replaced+=1
            self.latest[token]=(snap,int(slot),int(received_ns),generation)
            self.cv.notify()

    def superseded(self,token,generation):
        with self.cv:
            return int(self.latest_generation.get(token,generation))>int(generation)

    def newer_waiting(self,token,generation):
        return self.superseded(token,generation)

    def _price(self,token,row):
        snap,slot,received_ns,generation=row
        start_ms=max(0.0,(time.perf_counter_ns()-received_ns)/1e6)
        self.event_start_ms.append(start_ms)
        if start_ms>q20.MAX_START_AGE_MS:
            self.stale_drops+=1
            print("[ORACLE027_STALE_DROP] token=%s slot=%s age_ms=%.3f"%(
                token[:10],slot,start_ms
            ),flush=True)
            return

        t=time.perf_counter_ns()
        snap=materialize_snapshot(snap)
        materialize_ms=(time.perf_counter_ns()-t)/1e6
        self.materialize_ms.append(materialize_ms)

        self._warm(snap)
        started=time.perf_counter_ns()
        rows=[]

        for size in q20.FAST_SIZES:
            rows.extend(q18.exact_snapshot_opportunities(snap,size))
            self.evaluations+=2
            if self.superseded(token,generation):
                self.scan_replaced+=1
                print("[ORACLE027_GENERATION_DROP] token=%s slot=%s after_size=%.3f"%(
                    token[:10],slot,size
                ),flush=True)
                return

        best=max(rows,key=lambda x:x["local_net"])

        if float(best["local_bps"])>=q20.EXPAND_GATE_BPS:
            for size in q20.EXPAND_SIZES:
                rows.extend(q18.exact_snapshot_opportunities(snap,size))
                self.evaluations+=2
                if self.superseded(token,generation):
                    self.scan_replaced+=1
                    print("[ORACLE027_GENERATION_DROP] token=%s slot=%s after_size=%.3f"%(
                        token[:10],slot,size
                    ),flush=True)
                    return
            best=max(rows,key=lambda x:x["local_net"])

        if self.superseded(token,generation):
            self.end_generation_drops+=1
            print("[ORACLE027_END_GENERATION_DROP] token=%s slot=%s"%(
                token[:10],slot
            ),flush=True)
            return

        scan_ms=(time.perf_counter_ns()-started)/1e6
        self.scan_ms.append(scan_ms)
        self.processed+=1

        if int(best["local_net"])>0:
            self.positive+=1
        if self.best is None or int(best["local_net"])>int(self.best["local_net"]):
            self.best=dict(best)

        print(
            "[ORACLE027_EXACT_IMMUTABLE] token=%s slot=%s dir=%s size=%.3f "
            "bps=%+.2f net=%+d start_ms=%.3f materialize_ms=%.3f scan_ms=%.3f"
            %(token[:10],slot,best["direction"],float(best["size_sol"]),
              float(best["local_bps"]),int(best["local_net"]),start_ms,materialize_ms,scan_ms),
            flush=True,
        )

def patched_pair_snapshot(pair):
    return frozen_pair_snapshot(pair)

def install():
    q23.install_hot_token_net()
    q20._pair_snapshot=patched_pair_snapshot
    q20.LatestStateLane=ImmutableLatestStateLane
    return True

def _p99(rows):
    if not rows:
        return None
    s=sorted(rows)
    return s[min(len(s)-1,int(len(s)*.99))]

def run(seconds=60.0):
    root=Path.cwd()
    state,cap=q25.prepare_once(root)
    q25.bind_cached_state(state)
    q25.install_hot_math_and_prewarm(state)
    install()

    print("[ORACLE-027] IMMUTABLE SNAPSHOT + END-GENERATION GUARD",flush=True)
    print("[FREEZE] lb_pair + bin-array raw bytes copied at event submission",flush=True)
    print("[MATERIALIZE] private DLMM PoolState rebuilt inside pricing worker",flush=True)
    print("[GENERATION] latest submitted generation checked after every size and before publish",flush=True)
    print("[TOKEN_NET] ORACLE-023 persistent worker active",flush=True)
    print("[PRIVATE_KEY] not required",flush=True)
    print("[BROADCAST] disabled",flush=True)

    rc=q20.run(float(seconds))
    lane=q20._lane

    payload={
        "oracle_build":"ORACLE-027",
        "immutable_raw_snapshot":True,
        "end_generation_guard":True,
        "materialize_p99_ms":_p99(getattr(lane,"materialize_ms",[])),
        "end_generation_drops":int(getattr(lane,"end_generation_drops",0)),
        "processed":int(getattr(lane,"processed",0)),
        "positive":int(getattr(lane,"positive",0)),
        "p99_scan_ms":q20._p99(getattr(lane,"scan_ms",[])),
        "execution_authority":False,
        "paper_only":True,
        "real_money_moved":False,
        "broadcast":False,
    }
    out=Path("runtime_state/oracle/oracle_live_execution/oracle_027_immutable_snapshot_generation_guard.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[ORACLE027_COMPLETE] processed=%d positive=%d end_generation_drops=%d "
          "p99_materialize_ms=%s p99_scan_ms=%s"%(
              payload["processed"],payload["positive"],payload["end_generation_drops"],
              str(payload["materialize_p99_ms"]),str(payload["p99_scan_ms"])
          ),flush=True)
    print("[REPORT] %s"%out,flush=True)
    return rc

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=60.0)
    a=ap.parse_args(argv)
    return run(a.seconds)

if __name__=="__main__":
    raise SystemExit(main())
"""

test_src=r"""
import inspect,unittest
from qseries_v2.oracle_execution import oracle_027_immutable_snapshot_generation_guard as q27

class Dummy:
    token="T";pump_pool="P";meteora_pool="M";token_x="X";token_y="Y"
    decimals_x=6;decimals_y=9;pump_base_reserve=11;pump_quote_reserve=22
    lb_bytes=b"abc";arrays=[(0,"A",b"one"),(1,"B",b"two")]
    last_slot=7;last_event_ns=8

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q27.EXECUTION_AUTHORITY)
        self.assertTrue(q27.PAPER_ONLY)
        self.assertFalse(q27.REAL_MONEY_MOVED)

    def test_raw_snapshot_copies_bytes(self):
        p=Dummy()
        s=q27.frozen_pair_snapshot(p)
        self.assertEqual(s["lb_bytes"],b"abc")
        self.assertEqual(s["arrays_raw"][0][2],b"one")
        self.assertNotIn("dlmm_state",s)

    def test_generation_guard_tracks_latest_submit(self):
        lane=q27.ImmutableLatestStateLane()
        lane.submit("T",{},1,1)
        first=lane.latest_generation["T"]
        lane.submit("T",{},2,2)
        self.assertTrue(lane.superseded("T",first))

    def test_end_guard_present(self):
        s=inspect.getsource(q27.ImmutableLatestStateLane._price)
        self.assertIn("ORACLE027_END_GENERATION_DROP",s)
        self.assertIn("self.superseded(token,generation)",s)

    def test_materialize_uses_poolstate_from_accounts(self):
        s=inspect.getsource(q27.materialize_snapshot)
        self.assertIn("PoolState.from_accounts",s)
        self.assertIn('snap["arrays_raw"]',s)

    def test_q20_seams_patched(self):
        s=inspect.getsource(q27.install)
        self.assertIn("q20._pair_snapshot=patched_pair_snapshot",s)
        self.assertIn("q20.LatestStateLane=ImmutableLatestStateLane",s)

    def test_no_execution(self):
        s=inspect.getsource(q27)
        self.assertNotIn("sendTransaction",s)
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

run_src=r"""
from qseries_v2.oracle_execution.oracle_027_immutable_snapshot_generation_guard import main
if __name__=="__main__":
    raise SystemExit(main())
"""

MOD.write_text(textwrap.dedent(module_src).lstrip(),encoding="utf-8")
TEST.write_text(textwrap.dedent(test_src).lstrip(),encoding="utf-8")
RUN.write_text(textwrap.dedent(run_src).lstrip(),encoding="utf-8")

for f in (MOD,TEST,RUN):
    py_compile.compile(str(f),doraise=True)

print("[PASS] ORACLE-027 immutable snapshot + end-generation guard installed")
print("[FREEZE] raw LB-pair + bin-array bytes copied at submission")
print("[MATERIALIZE] private PoolState rebuilt only in pricing worker")
print("[GENERATION] latest submitted token generation checked before publish")
print("[TOKEN_NET] ORACLE-023 persistent worker retained")
print("[PRIVATE_KEY] not required")
print("[BROADCAST] disabled")
print("[OWNER] ORACLE")
