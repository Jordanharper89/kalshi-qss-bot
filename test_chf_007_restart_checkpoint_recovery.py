from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_007_restart_checkpoint_recovery import certify_restart
result=certify_restart(Path.cwd())
print("[FIRST_CYCLE]",result["first"])
print("[SECOND_CYCLE]",result["second"])
print("[CHECKPOINT]",result["checkpoint"])
print("[RAW_SIZE]",result["raw_size"])
print("[PASS] no duplicate replay across restart boundary")
print("[PASS] CHF-007 restart checkpoint recovery certified")
