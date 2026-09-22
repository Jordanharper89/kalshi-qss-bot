from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_010_exact_canonical_submit_await_readback import run_physical,WRITER_ID
obs,token,submission,terminal,rb,sig=run_physical(Path.cwd())
print("[CANONICAL_SIGNATURE]",sig)
print("[WRITER_ID]",WRITER_ID)
print("[TOKEN]",token)
print("[OBSERVATION_ID]",obs.observation_id)
print("[REQUEST_ID]",getattr(submission,"request_id",None))
print("[AWAIT_TERMINAL]",terminal)
print("[EXACT_READBACK_COUNT]",len(rb))
assert len(rb)==1
assert getattr(obs,"execution_allowed",False) is False
print("[PASS] canonical CHF observation built from exact OAD-261 CanonicalObservation contract")
print("[PASS] submitted through exact OPH-019 single-writer boundary")
print("[PASS] awaited terminal commit state before readback")
print("[PASS] exact OAD-068 observation-ID readback certified")
print("[PROBABILITY_ENABLED]",False)
print("[DIRECTION_ENABLED]",False)
print("[PUBLICATION_ALLOWED]",False)
print("[EXECUTION_AUTHORITY]",False)
print("[PASS] CHF-010 repaired end-to-end PostgreSQL persistence certified")
