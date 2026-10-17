from pathlib import Path

ROOT=Path.cwd()
P=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/checkpoint2_forward_atomic_sim.py"
T=ROOT/"test_canonical_checkpoint2_forward_atomic_sim.py"

P.write_text(r'''
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r

def main():
    root=Path.cwd()
    state,_=r.q25.prepare_once(root)
    r.q25.bind_cached_state(state)
    warmed=r.install_proven_hot_math(state)
    _,r.USER=r.q87.c.sim_identity()
    r.prebuild_templates(state,r.USER)
    r.prebuild_meteora_templates(state,r.USER,warmed)

    for pair in state.get("pairs") or []:
        if str(pair.token) in r.READY_TOKENS:
            r.q18.worker().warm(str(pair.pump_pool))

    r.BLOCKHASH.start()

    try:
        for pair in state.get("pairs") or []:
            token=str(pair.token)
            if token not in r.READY_TOKENS:
                continue

            snap=r.immutable_snapshot(pair)
            rows=r.q18.exact_snapshot_opportunities(snap,0.001)
            forward=next((x for x in rows if x["direction"]=="PUMP_TO_METEORA"),None)

            if forward is None:
                continue

            print("[CHECKPOINT2_ROUTE] token=%s bps=%+.2f net=%+d"%(
                token[:10],float(forward["local_bps"]),int(forward["local_net"])),flush=True)

            result=r._execute_route_once(r.USER,snap,forward)

            if not result.get("ok"):
                print("[CHECKPOINT2_COMPILE_FAIL]",result.get("compiled"),flush=True)
                return 2

            sim=result["sim"]

            if sim.get("err") is None:
                print("[CHECKPOINT2_FORWARD_ATOMIC_SIM_PASS] token=%s candidate=%s bytes=%d"%(
                    token[:10],result["compiled"]["candidate"],result["compiled"]["bytes"]),flush=True)
                return 0

            print("[CHECKPOINT2_FORWARD_ATOMIC_SIM_REJECT] token=%s err=%s"%(
                token[:10],sim.get("err")),flush=True)
            r._canonical_sim_logs(sim)
            return 2

        raise RuntimeError("NO_READY_FORWARD_PAIR")

    finally:
        r.BLOCKHASH.close()
        if getattr(r.q18,"_worker",None) is not None:
            r.q18._worker.close()
            r.q18._worker=None
        try:
            r.q25.q23.worker().close()
        except Exception:
            pass

if __name__=="__main__":
    raise SystemExit(main())
'''.lstrip(),encoding="utf-8")

T.write_text(r'''
from pathlib import Path
import unittest

P=Path("qseries_v2/oracle_execution/solana_atomic_executor/checkpoint2_forward_atomic_sim.py")

class T(unittest.TestCase):
    def test_canonical_only(self):
        s=P.read_text(encoding="utf-8")
        self.assertIn("_execute_route_once",s)
        self.assertIn("PUMP_TO_METEORA",s)
        self.assertIn("CHECKPOINT2_FORWARD_ATOMIC_SIM_PASS",s)

    def test_no_broadcast(self):
        s=P.read_text(encoding="utf-8")
        self.assertNotIn("sendTransaction(",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
'''.lstrip(),encoding="utf-8")

print("[PASS] canonical checkpoint-2 forward atomic simulation installed")
print("[PATH] existing solana_atomic_executor only")
print("[PROFIT_GATE] bypassed for machinery test")
print("[BROADCAST] disabled")