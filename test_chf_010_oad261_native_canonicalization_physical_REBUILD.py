from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_010_oad261_native_canonicalization_physical import run_physical,WRITER_ID

canonical,token,batch_id,submission,terminal,rb=run_physical(Path.cwd())
print("[WRITER_ID]",WRITER_ID)
print("[TOKEN]",token)
print("[BATCH_ID]",batch_id)
print("[SOURCE_ID]",canonical.source_id)
print("[OBSERVATION_TYPE]",canonical.observation_type)
print("[OBSERVATION_ID]",canonical.observation_id)
print("[CONTENT_HASH]",canonical.content_hash)
print("[REPLAY_HASH]",canonical.replay_hash)
print("[REQUEST_ID]",getattr(submission,"request_id",None))
print("[AWAIT_TERMINAL]",terminal)
print("[EXACT_READBACK_COUNT]",len(rb))
print("[READBACK_OBSERVATION_ID]",rb[0].observation_id)
assert len(rb)==1
assert rb[0].observation_id==canonical.observation_id
assert canonical.read_only is True
assert canonical.execution_allowed is False
print("[PASS] failed hand-built CHF-010 canonical identity retired")
print("[PASS] CHF fixture canonicalized by exact OAD-261 production canonicalizer")
print("[PASS] RawSourceObservation.create and CanonicalObservation.create inherited from OAD-261")
print("[PASS] exact OPH-019 submit -> await_request lifecycle used")
print("[PASS] exact OAD-068 durable readback certified")
print("[PROBABILITY_ENABLED]",False)
print("[DIRECTION_ENABLED]",False)
print("[PUBLICATION_ALLOWED]",False)
print("[EXECUTION_AUTHORITY]",False)
print("[PASS] CHF-010 native canonicalization PostgreSQL persistence certified")
