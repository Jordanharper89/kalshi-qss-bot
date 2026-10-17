from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_031_chain_truth_live_bridge.py")

s=R.read_text(encoding="utf-8")
tree=ast.parse(s)
lines=s.splitlines()

fn=next((n for n in tree.body
 if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
 and n.name=="fast_live_attack"),None)
if fn is None:
    raise RuntimeError("MRY031_FAST_LIVE_ATTACK_MISSING")

new = '''def fast_live_attack(lane,token,snap,opportunity,slot,received_ns,generation):
    refreshed=_fast_010_refresh_latest(
        lane,token,snap,opportunity,slot,received_ns,generation)
    if refreshed is None:
        return

    snap,opportunity,slot,received_ns,generation=refreshed
    direction=str(opportunity["direction"])

    if int(opportunity["start"])!=CANARY_TRADE_LAMPORTS:
        return

    required_final=(
        CANARY_TRADE_LAMPORTS
        +FAST_010_FEE_CEILING_LAMPORTS
        +FAST_010_MIN_REALIZED_LAMPORTS
    )

    def build_locked(opp):
        route=same_snapshot_route(USER,snap,opp)
        route["direction"]=direction
        locked_route,old_bound,new_bound=_fast_010_profit_lock_route(
            route,direction,required_final)
        compiled=compile_current(USER,locked_route)
        if not compiled.get("ok"):
            raise RuntimeError(
                "FAST_010_COMPILE:"+str(compiled.get("reason","UNKNOWN")))
        fee=int(compiled.get("fee_lamports") or FAST_010_FEE_CEILING_LAMPORTS)
        if fee>FAST_010_FEE_CEILING_LAMPORTS:
            raise RuntimeError("FAST_010_FEE_ABOVE_CEILING:"+str(fee))
        if len(compiled.get("raw") or b"")>MAX_TX_BYTES:
            raise RuntimeError("FAST_010_PACKET_TOO_LARGE")
        return compiled,old_bound,new_bound,fee

    conservative=int(opportunity["local_net"])-FAST_010_FEE_CEILING_LAMPORTS
    if conservative<FAST_010_MIN_REALIZED_LAMPORTS:
        print("[FAST_010_HOLD] token=%s dir=%s reason=BELOW_FLOOR after_fee=%+d"%
              (token[:10],direction,conservative),flush=True)
        return

    try:
        locked,old_bound,new_bound,fee=build_locked(opportunity)
    except Exception as exc:
        print("[FAST_010_BUILD_REJECT] token=%s dir=%s error=%s:%s"%
              (token[:10],direction,type(exc).__name__,str(exc)[:240]),flush=True)
        return

    if direction=="PUMP_TO_METEORA":
        try:
            sim=simulate_current(locked,USER)
        except Exception as exc:
            print("[FAST_010_SIM_RPC_REJECT] token=%s error=%s:%s"%
                  (token[:10],type(exc).__name__,str(exc)[:220]),flush=True)
            return

        if sim.get("err") is not None:
            actual=pump_6040_actual_base_out(sim)
            if actual is None:
                print("[FAST_010_SIM_REJECT] token=%s err=%s"%
                      (token[:10],str(sim.get("err"))),flush=True)
                _canonical_sim_logs(sim)
                return

            corrected=reprice_from_pump_chain_truth(snap,opportunity,actual)
            corrected_after=(
                int(corrected["local_net"])
                -FAST_010_FEE_CEILING_LAMPORTS
            )

            print("[FAST_010_6040_CHAIN_TRUTH] token=%s base_out=%d old_bps=%+.2f corrected_bps=%+.2f after_fee=%+d"%
                  (token[:10],int(actual),float(opportunity["local_bps"]),
                   float(corrected["local_bps"]),corrected_after),flush=True)

            if corrected_after<FAST_010_MIN_REALIZED_LAMPORTS:
                print("[FAST_010_6040_HOLD] token=%s reason=CORRECTED_BELOW_FLOOR"%
                      token[:10],flush=True)
                return

            if lane.newer_waiting(token,generation):
                print("[FAST_010_6040_HOLD] token=%s reason=SUPERSEDED_BEFORE_REBUILD"%
                      token[:10],flush=True)
                return

            try:
                locked,old_bound,new_bound,fee=build_locked(corrected)
                sim2=simulate_current(locked,USER)
            except Exception as exc:
                print("[FAST_010_6040_REBUILD_REJECT] token=%s error=%s:%s"%
                      (token[:10],type(exc).__name__,str(exc)[:220]),flush=True)
                return

            if sim2.get("err") is not None:
                print("[FAST_010_6040_SECOND_SIM_REJECT] token=%s err=%s"%
                      (token[:10],str(sim2.get("err"))),flush=True)
                _canonical_sim_logs(sim2)
                return

            opportunity=corrected
            conservative=int(corrected["local_net"])-fee
            print("[FAST_010_6040_REBUILD_PASS] token=%s corrected_bps=%+.2f fee=%d after_fee=%+d"%
                  (token[:10],float(corrected["local_bps"]),fee,conservative),
                  flush=True)
        else:
            conservative=int(opportunity["local_net"])-fee
            print("[FAST_010_FORWARD_SIM_PASS] token=%s bps=%+.2f fee=%d after_fee=%+d"%
                  (token[:10],float(opportunity["local_bps"]),fee,conservative),
                  flush=True)
    else:
        conservative=int(opportunity["local_net"])-fee

    if conservative<FAST_010_MIN_REALIZED_LAMPORTS:
        print("[FAST_010_HOLD] token=%s reason=FINAL_AFTER_FEE_BELOW_FLOOR after_fee=%+d"%
              (token[:10],conservative),flush=True)
        return

    age_ms=(time.perf_counter_ns()-received_ns)/1e6
    print("[FAST_010_READY] token=%s dir=%s slot=%s conservative_after_fee=%+d profit_floor=%d fee=%d old_final_bound=%d locked_final_bound=%d bytes=%d event_age_ms=%.3f chain_truth=%s"%
          (token[:10],direction,slot,conservative,FAST_010_MIN_REALIZED_LAMPORTS,
           fee,old_bound,new_bound,int(locked["bytes"]),age_ms,
           bool(opportunity.get("pump_chain_truth"))),flush=True)

    _live_010_certify_or_send(
        lane,token,direction,slot,received_ns,generation,locked,conservative)
'''

lines[fn.lineno-1:fn.end_lineno]=new.splitlines()
out="\n".join(lines)+"\n"
ast.parse(out)

for needle in (
    '"skipPreflight":False',
    '"maxRetries":0',
    'CANARY_TRADE_LAMPORTS=10_000_000',
    'FAST_010_MIN_REALIZED_LAMPORTS=10_000',
    'def pump_6040_actual_base_out',
    'def reprice_from_pump_chain_truth',
):
    if needle not in out:
        raise RuntimeError("MRY031_SAFETY_OR_DEPENDENCY_MISSING:"+needle)

R.write_text(out,encoding="utf-8")

test='''import ast,unittest\nfrom pathlib import Path\nR=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")\nclass T(unittest.TestCase):\n def test_runtime_parses(self):\n  ast.parse(R.read_text(encoding="utf-8"))\n def test_chain_truth_live_bridge(self):\n  s=R.read_text(encoding="utf-8")\n  a=s.index("def fast_live_attack")\n  b=s.index("\\ndef ",a+5)\n  f=s[a:b]\n  self.assertIn("simulate_current(locked,USER)",f)\n  self.assertIn("pump_6040_actual_base_out(sim)",f)\n  self.assertIn("reprice_from_pump_chain_truth(snap,opportunity,actual)",f)\n  self.assertIn("FAST_010_6040_REBUILD_PASS",f)\n  self.assertEqual(f.count("lane.newer_waiting(token,generation)"),1)\n def test_no_blind_slippage_widening(self):\n  s=R.read_text(encoding="utf-8")\n  a=s.index("def fast_live_attack")\n  b=s.index("\\ndef ",a+5)\n  f=s[a:b]\n  self.assertNotIn("FAST_010_PUMP_EXECUTION_TOLERANCE_BPS",f)\n  self.assertIn("corrected_after<FAST_010_MIN_REALIZED_LAMPORTS",f)\n def test_money_and_send_guards(self):\n  s=R.read_text(encoding="utf-8")\n  self.assertIn('"skipPreflight":False',s)\n  self.assertIn('"maxRetries":0',s)\n  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)\nif __name__=="__main__": unittest.main(verbosity=2)\n'''
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-031 installed")
print("[PASS] 0.010 live path consumes Pump 6040 chain truth")
print("[PASS] corrected route rebuilt once and re-simulated before send")
print("[PASS] no blind slippage widening; profit floor preserved")
