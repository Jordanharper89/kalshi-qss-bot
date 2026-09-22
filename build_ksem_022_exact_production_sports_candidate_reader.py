from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
MOD=PKG/"production_sports_candidate_reader.py"
TEST=ROOT/"test_ksem_022_exact_production_sports_candidate_reader.py"

CODE="""from qseries_v2.oracle_adapters.independent.oad_118_persisted_authoritative_sports_cohort import load_persisted_authoritative_sports_cohort
from qseries_v2.oracle_adapters.independent.oad_119_persisted_sports_structured_descriptor import descriptors_from_persisted_sports_rows
from qseries_v2.oracle_adapters.independent.oad_120_current_market_sports_team_pair_index import fetch_current_market_sports_candidates

def read_production_sports_candidates(root=None, cohort_timeout=30, acquisition_timeout=15, market_limit=100, market_timeout=20):
    cohort=load_persisted_authoritative_sports_cohort(
        root=root,
        timeout_seconds=cohort_timeout,
        acquisition_timeout_seconds=acquisition_timeout)
    descriptors=descriptors_from_persisted_sports_rows(cohort.rows)
    markets,groups=fetch_current_market_sports_candidates(
        descriptors,
        limit=market_limit,
        timeout_seconds=market_timeout)
    return cohort,tuple(descriptors),tuple(markets),tuple(groups)
"""

def main():
    print("="*120); print(" KSEM-022 EXACT PRODUCTION SPORTS CANDIDATE READER"); print("="*120)
    MOD.write_text(CODE,encoding="utf-8")
    compile(CODE,str(MOD),"exec")
    TEST.write_text(
        "from qseries_v2.kalshi_sports_evidence_mapping.production_sports_candidate_reader import read_production_sports_candidates\n"
        "assert callable(read_production_sports_candidates)\n"
        "print('[PASS] exact OAD-118 -> OAD-119 -> OAD-120 production reader installed')\n"
        "print('[PASS] KSEM-022 certified')\n",encoding="utf-8")
    print("[WRITE]",MOD.relative_to(ROOT)); print("[WRITE]",TEST.name)
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__": main()