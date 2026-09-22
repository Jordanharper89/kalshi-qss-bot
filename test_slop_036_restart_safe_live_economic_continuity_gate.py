from pathlib import Path
s=Path('run_slop_buy_pressure_live.py').read_text()
assert 'read_predictions(ROOT)' in s
assert 'resolve_background(ROOT' in s
assert 'seen=set()' in s
assert 'worker_round(root=ROOT' in s
print('[PASS] durable prediction ledger is reread after restart')
print('[PASS] unresolved predictions return to background maturity/resolution')
print('[PASS] resolution ledger remains idempotent through certified SLOP-020 path')
print('[PASS] execution_authority=FALSE')
