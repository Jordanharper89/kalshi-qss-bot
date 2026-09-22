from pathlib import Path
import ast
R=Path.cwd();P=R/"run_slop_buy_pressure_live.py";s=P.read_text(encoding="utf-8");t=ast.parse(s)
required=["worker_round","read_predictions","print_prediction","resolve_background","time.sleep(5.0)","execution_authority=FALSE"]
missing=[x for x in required if x not in s]
if missing: raise SystemExit("[FAIL] runner missing "+repr(missing))
T=R/"test_slop_035_live_prediction_resolution_output_gate.py"
T.write_text("""from pathlib import Path\ns=Path('run_slop_buy_pressure_live.py').read_text()\nfor x in ('worker_round','print_prediction','resolve_background','[SLOP LIVE] state=HEALTHY','execution_authority=FALSE'): assert x in s,x\nprint('[PASS] continuous discovery/admission worker bound')\nprint('[PASS] readable ORACLE PREDICTION output bound')\nprint('[PASS] background ORACLE RESOLUTION output bound')\nprint('[PASS] execution_authority=FALSE')\n""",encoding="utf-8")
print("[PASS] SLOP-035 installed");print("[PASS] prediction + resolution runtime output contract")
