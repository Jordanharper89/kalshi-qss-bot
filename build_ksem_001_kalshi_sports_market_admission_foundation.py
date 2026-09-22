from pathlib import Path
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
TEST=ROOT/"test_ksem_001_kalshi_sports_market_admission_foundation.py"
def main():
    print("="*110); print(" KSEM-001 KALSHI SPORTS MARKET ADMISSION FOUNDATION"); print("="*110)
    osn=ROOT/"qseries_v2/oracle_source_network/state/osn100_final_native_sports_production_certification.json"
    if not osn.exists(): raise SystemExit("[FAIL] missing certified OSN-100 state")
    import json
    d=json.loads(osn.read_text(encoding="utf-8"))
    if not (d.get("sports_source_activation_complete") and d.get("execution_authority") is False): raise SystemExit("[FAIL] OSN-100 state invalid")
    PKG.mkdir(parents=True,exist_ok=True); (PKG/"state").mkdir(exist_ok=True); (PKG/"__init__.py").touch()
    mod=PKG/"sports_market_admission.py"
    mod.write_text("from dataclasses import dataclass\n@dataclass(frozen=True)\nclass SportsMarketAdmission:\n ticker:str; admitted:bool; sport:str|None; league:str|None; reasons:tuple; execution_authority:bool=False\ndef admit_from_classification(ticker,*,is_sports,sport=None,league=None,reasons=()):\n ok=bool(ticker and is_sports and (sport or league)); rs=tuple(reasons)\n if is_sports and not ok: rs=rs+(\'SPORT_OR_LEAGUE_UNRESOLVED\',)\n return SportsMarketAdmission(str(ticker),ok,sport,league,rs,False)\n",encoding="utf-8")
    compile(mod.read_text(),str(mod),"exec")
    state=PKG/"state/ksem001_admission_foundation.json"; state.write_text(json.dumps({"osn100_verified":True,"execution_authority":False},indent=2))
    print("[PASS] OSN-100 verified read-only"); print("[WRITE]",mod.relative_to(ROOT))
    TEST.write_text("from qseries_v2.kalshi_sports_evidence_mapping.sports_market_admission import admit_from_classification\nassert admit_from_classification('KX',is_sports=True,sport='football',league='NFL').admitted\nassert not admit_from_classification('KX',is_sports=False).admitted\nassert not admit_from_classification('KX',is_sports=True).admitted\nprint('[PASS] sports admission is explicit and fail-closed')\nprint('[PASS] KSEM-001 certified')\n",encoding="utf-8")
    compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
    print("[WRITE]",TEST.name)
    print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()
