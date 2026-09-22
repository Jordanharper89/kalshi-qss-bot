
from qseries_v2.oracle_source_network.certification.ncaab_dynamic_activation_gate import activate
r=activate()
print("[NCAAB_ACTIVATION]",r)
assert r.execution_authority is False
assert r.status in (
    "PHYSICAL_EXTRACTING",
    "EXACT_EXTRACTOR_READY_CURRENT_PAGE_EMPTY",
    "CERTIFIED_TEST_NOT_FOUND",
)
if r.status=="PHYSICAL_EXTRACTING":
    assert r.events>0 and r.admitted is True
    print("[PASS] NCAAB dynamically activated by existing certified physical extractor")
elif r.status=="EXACT_EXTRACTOR_READY_CURRENT_PAGE_EMPTY":
    assert r.events==0 and r.admitted is False
    print("[HOLD] NCAAB remains correctly held because current official page is empty")
else:
    assert r.admitted is False
    print("[HOLD] NCAAB exact certified test filename not present; no synthetic admission")
print("[PASS] OSN-056 NCAAB dynamic activation truth gate certified")
