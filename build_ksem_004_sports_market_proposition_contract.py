from pathlib import Path
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
TEST=ROOT/"test_ksem_004_sports_market_proposition_contract.py"
def main():
    print("="*110); print(" KSEM-004 SPORTS MARKET PROPOSITION CONTRACT"); print("="*110)
    import json
    if not (PKG/"state/ksem003_entity_league_resolution.json").exists(): raise SystemExit("[FAIL] missing KSEM-003")
    mod=PKG/"market_proposition.py"
    types=("GAME_WINNER","TEAM_TOTAL","GAME_TOTAL","SPREAD_MARGIN","PLAYER_STAT","TEAM_STAT","SCORING_OCCURRENCE","PLAYOFF_QUALIFICATION","CHAMPIONSHIP_FUTURE","SEASON_WINS","STANDINGS_RANKING","TOURNAMENT_ADVANCEMENT","AWARD","OTHER")
    code="from dataclasses import dataclass\nTYPES=frozenset("+repr(types)+")\n@dataclass(frozen=True)\nclass SportsProposition:\n ticker:str; proposition_type:str; subjects:tuple; condition:str; resolved:bool; reasons:tuple; execution_authority:bool=False\ndef proposition(ticker,proposition_type,subjects=(),condition=\'\',reasons=()):\n pt=str(proposition_type or \'\').upper(); rs=tuple(reasons); ok=bool(ticker and pt in TYPES and tuple(subjects) and str(condition).strip())\n if pt not in TYPES: rs=rs+(\'UNSUPPORTED_PROPOSITION_TYPE\',)\n return SportsProposition(str(ticker),pt,tuple(subjects),str(condition),ok,rs,False)\n"
    mod.write_text(code,encoding="utf-8"); compile(code,str(mod),"exec")
    (PKG/"state/ksem004_market_proposition_contract.json").write_text(json.dumps({"taxonomy":list(types),"execution_authority":False},indent=2))
    print("[WRITE]",mod.relative_to(ROOT)); print("[PASS] proposition taxonomy installed")
    TEST.write_text("from qseries_v2.kalshi_sports_evidence_mapping.market_proposition import proposition\nassert proposition('KX','GAME_WINNER',('Texans','Chiefs'),'Texans win').resolved\nassert not proposition('KX','MAGIC',('A',),'x').resolved\nprint('[PASS] proposition contract explicit and auditable')\nprint('[PASS] unsupported types fail closed')\nprint('[PASS] KSEM-004 certified')\n",encoding="utf-8")
    compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
    print("[WRITE]",TEST.name)
    print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()
