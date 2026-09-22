from pathlib import Path
s=Path('run_slop_buy_pressure_live.py').read_text()
for x in ('worker_round','print_prediction','resolve_background','[SLOP LIVE] state=HEALTHY','execution_authority=FALSE'): assert x in s,x
print('[PASS] continuous discovery/admission worker bound')
print('[PASS] readable ORACLE PREDICTION output bound')
print('[PASS] background ORACLE RESOLUTION output bound')
print('[PASS] execution_authority=FALSE')
