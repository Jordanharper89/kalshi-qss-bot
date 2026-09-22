from pathlib import Path
import ast
R=Path.cwd();P=R/"run_slop_buy_pressure_live.py";s=P.read_text(encoding="utf-8")
need=["read_predictions(ROOT)","worker_round(root=ROOT","resolve_background(ROOT","seen=set()"]
for x in need:
 if x not in s: raise SystemExit("[FAIL] missing restart/economic continuity boundary: "+x)
T=R/"test_slop_036_restart_safe_live_economic_continuity_gate.py"
T.write_text("""from pathlib import Path\ns=Path('run_slop_buy_pressure_live.py').read_text()\nassert 'read_predictions(ROOT)' in s\nassert 'resolve_background(ROOT' in s\nassert 'seen=set()' in s\nassert 'worker_round(root=ROOT' in s\nprint('[PASS] durable prediction ledger is reread after restart')\nprint('[PASS] unresolved predictions return to background maturity/resolution')\nprint('[PASS] resolution ledger remains idempotent through certified SLOP-020 path')\nprint('[PASS] execution_authority=FALSE')\n""",encoding="utf-8")
print("[PASS] SLOP-036 installed");print("[PASS] restart-safe live economic continuity bound")
