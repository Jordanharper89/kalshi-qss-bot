
from qseries_v2.oracle_source_network.certification.sports_event_extraction_truth_v2 import rows
r=rows()
for x in r: print("[TRUTH]",x)
admitted=tuple(x.league for x in r if x.admitted)
assert admitted==("NFL","NCAAF","NBA")
assert all(x.execution_authority is False for x in r)
assert next(x for x in r if x.league=="NCAAB").state=="EXACT_EXTRACTOR_READY_CURRENT_PAGE_EMPTY"
assert next(x for x in r if x.league=="UCL").state=="BLOCKED"
print("[PASS] admitted physical event extraction leagues:",admitted)
print("[PASS] OSN-049 sports extraction truth registry certified")
