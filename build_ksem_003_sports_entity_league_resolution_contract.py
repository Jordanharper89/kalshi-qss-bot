from pathlib import Path
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
TEST=ROOT/"test_ksem_003_sports_entity_league_resolution_contract.py"
def main():
    print("="*110); print(" KSEM-003 SPORTS ENTITY LEAGUE RESOLUTION CONTRACT"); print("="*110)
    import json
    inv=PKG/"state/ksem002_existing_classifier_inventory.json"
    if not inv.exists(): raise SystemExit("[FAIL] missing KSEM-002")
    mod=PKG/"entity_league_resolution.py"
    mod.write_text("from dataclasses import dataclass\n@dataclass(frozen=True)\nclass EntityLeagueResolution:\n ticker:str; league:str|None; entities:tuple; resolved:bool; ambiguity:tuple; execution_authority:bool=False\ndef resolve_from_existing(ticker,*,league=None,entities=(),ambiguity=()):\n es=tuple(dict.fromkeys(str(x).strip() for x in entities if str(x).strip())); amb=tuple(ambiguity); ok=bool(ticker and league and es and not amb)\n return EntityLeagueResolution(str(ticker),league,es,ok,amb,False)\n",encoding="utf-8")
    compile(mod.read_text(),str(mod),"exec")
    d=json.loads(inv.read_text()); (PKG/"state/ksem003_entity_league_resolution.json").write_text(json.dumps({"physical_candidates":d["count"],"ambiguity_policy":"REJECT","execution_authority":False},indent=2))
    print("[PASS] physical inventory consumed read-only"); print("[WRITE]",mod.relative_to(ROOT))
    TEST.write_text("from qseries_v2.kalshi_sports_evidence_mapping.entity_league_resolution import resolve_from_existing\nassert resolve_from_existing('KX',league='NFL',entities=('Texans','Chiefs')).resolved\nassert not resolve_from_existing('KX',league='NFL',entities=('Texans',),ambiguity=('MULTIPLE_MATCHES',)).resolved\nprint('[PASS] entity/league resolution fail-closes ambiguity')\nprint('[PASS] KSEM-003 certified')\n",encoding="utf-8")
    compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
    print("[WRITE]",TEST.name)
    print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()
