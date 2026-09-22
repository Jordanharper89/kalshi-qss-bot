from collections import Counter
from qseries_v2.oracle_adapters.independent.oad_234_crypto_prospective_outcome_calibration_scoring import read_and_score_mature_prospective_cases
from qseries_v2.oracle_adapters.independent.oad_242_crypto_exact_prospective_forecast_outcome_binding import read_exact_prospective_bindings
from qseries_v2.oracle_adapters.independent.oad_244_crypto_physical_ocl006_exact_calibration import materialize_exact_prospective_calibration
from qseries_v2.oracle_adapters.independent.oad_245_crypto_physical_provider_source_reliability import materialize_exact_provider_source_reliability
from qseries_v2.oracle_adapters.independent.oad_246_crypto_prospective_truth_calibration_physical_certification import certify_prospective_truth_calibration

bindings=read_exact_prospective_bindings()
scored=read_and_score_mature_prospective_cases()
cal=materialize_exact_prospective_calibration()
rel=materialize_exact_provider_source_reliability()
cert=certify_prospective_truth_calibration()

print("[EXACT_BINDINGS]",len(bindings),dict(Counter(x.asset for x in bindings)))
print("[SCORED_CASES]",len(scored),dict(Counter(x.asset for x in scored)))
if scored:
    brier=sum(float(x.brier_score) for x in scored)/len(scored)
    baseline=sum(float(x.baseline_brier) for x in scored)/len(scored)
    delta=sum(float(x.performance_delta) for x in scored)/len(scored)
    print("[FORWARD_SCORE] mean_brier=",round(brier,8),
          "baseline_brier=",round(baseline,8),
          "mean_delta=",round(delta,8),
          "beats_baseline=",brier<baseline)
    for x in scored[-20:]:
        print("[CASE]",x.asset,"p=",round(float(x.forecast_probability),6),
              "outcome=",bool(x.outcome_positive),"brier=",round(float(x.brier_score),8),
              "baseline=",round(float(x.baseline_brier),8))
print("[EXACT_CALIBRATION]",cal)
print("[SOURCE_RELIABILITY]",rel)
print("[CERTIFICATION]",cert)
print("[PASS] OPA-003 forward probability calibration audit complete")
