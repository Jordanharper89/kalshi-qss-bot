from qseries_v2.oracle_source_network.certification.final_exact_sports_source_binding_certification import certify_exact_source_binding

r = certify_exact_source_binding()
print("[FINAL_EXACT_SOURCE_BINDING]", r)

assert r.interfaces_captured is True
assert r.bindings_verified is True
assert r.physical_cycle_passed is True
assert r.activation_truth_frozen is True
assert r.direct_runtime_callable_activation is False
assert r.admitted == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")
assert r.held == ("NCAAB", "MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED")
assert r.blocked == ("UCL",)
assert r.execution_authority is False

print("[PASS] repaired OSN-071 certification retained")
print("[PASS] exact source binding discovery retained")
print("[PASS] bounded physical source cycle retained")
print("[PASS] honest activation registry retained")
print("[PASS] no false direct runtime activation claim made")
print("[PASS] OSN-075 repaired final exact source-binding certification complete")
