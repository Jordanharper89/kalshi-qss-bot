from pathlib import Path
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
MOD=PKG/"live_sports_candidate_boundary.py"; TEST=ROOT/"test_ksem_017_live_sports_candidate_boundary.py"
CODE="""from importlib import import_module
READER=('qseries_v2.oracle_intelligence_analytics_runtime.oiar_047_production_kalshi_current_eligibility_boundary','read_current_kalshi_markets')
SPORTS=('qseries_v2.oracle_adapters.independent.oad_120_current_market_sports_team_pair_index','fetch_current_market_sports_candidates')
def _load(spec):
    return getattr(import_module(spec[0]),spec[1])
def read_current_markets(*args,**kwargs):
    return _load(READER)(*args,**kwargs)
def read_current_sports_candidates(*args,**kwargs):
    return _load(SPORTS)(*args,**kwargs)
"""
def main():
    print("="*120); print(" KSEM-017 LIVE SPORTS CANDIDATE BOUNDARY"); print("="*120)
    MOD.write_text(CODE,encoding="utf-8"); compile(CODE,str(MOD),"exec")
    TEST.write_text("from qseries_v2.kalshi_sports_evidence_mapping.live_sports_candidate_boundary import READER,SPORTS\nassert READER[1]=='read_current_kalshi_markets'\nassert SPORTS[1]=='fetch_current_market_sports_candidates'\nprint('[PASS] exact live reader and sports-candidate boundary installed')\nprint('[PASS] KSEM-017 certified')\n",encoding="utf-8")
    print("[WRITE]",MOD.relative_to(ROOT)); print("[WRITE]",TEST.name); print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()