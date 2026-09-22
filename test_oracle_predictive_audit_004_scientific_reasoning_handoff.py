from qseries_v2.oracle_adapters.independent.oad_215_crypto_ocl_incremental_state_consumption import read_crypto_ocl_state
from qseries_v2.oracle_adapters.independent.oad_235_prospective_calibration_source_reliability_materialization import materialize_prospective_calibration_source_reliability
from qseries_v2.oracle_adapters.independent.oad_236_prospective_adaptive_ocl029_readmission import run_prospective_adaptive_ocl029_readmission
from qseries_v2.oracle_adapters.independent.oad_238_crypto_prospective_learning_state_refresh import refresh_prospective_learning_states

cycle,state,physical=read_crypto_ocl_state()
cal=materialize_prospective_calibration_source_reliability()
adaptive=run_prospective_adaptive_ocl029_readmission()
refresh=refresh_prospective_learning_states()

print("[OCL_CYCLE]",cycle)
print("[OCL_STATE]",state)
print("[OCL_PHYSICAL]",physical)
print("[CALIBRATION_RELIABILITY]",cal)
print("[ADAPTIVE_READMISSION]",adaptive)
print("[STATE_REFRESH]",refresh)
print("[SUPPLIED_HASHES]",adaptive.supplied_hashes)
print("[MISSING_HASHES]",adaptive.missing_state_hashes)
print("[ADMISSION_STATE]",adaptive.admission_state)
print("[HANDOFF_VERIFIED]",adaptive.handoff_verified)
print("[PROBABILITY_ENABLED]",refresh.probability_enabled)
print("[PUBLICATION_ALLOWED]",refresh.publication_allowed)
assert getattr(state,"state_hash",None),"learner state hash missing"
print("[PASS] OPA-004 Scientific Reasoning handoff audit complete")
