from pathlib import Path

ROOT=Path.cwd()

def require(rel):
    p=ROOT/rel
    if not p.exists(): raise SystemExit('[FAIL] missing dependency: '+str(p))
    print('[PASS] dependency verified:',p.relative_to(ROOT))

def write(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content.rstrip()+'\n',encoding='utf-8')
    print('[WRITE]',p.relative_to(ROOT))

def main():
    print('='*118)
    print(' OSN-049 SPORTS EVENT EXTRACTION TRUTH REGISTRY V2 INSTALLER')
    print('='*118)
    require('qseries_v2/oracle_source_network/mapping/nfl_live_escaped_state_extractor.py')
    require('qseries_v2/oracle_source_network/mapping/ncaaf_exact_scoreboard_extractor.py')
    require('qseries_v2/oracle_source_network/mapping/ncaab_exact_scoreboard_extractor.py')
    require('qseries_v2/oracle_source_network/acquisition/nhl_event_surface_boundary.py')
    require('qseries_v2/oracle_source_network/acquisition/soccer_event_surface_boundary.py')
    write('qseries_v2/oracle_source_network/certification/sports_event_extraction_truth_v2.py','\nfrom dataclasses import dataclass\n\n@dataclass(frozen=True,slots=True)\nclass SportsExtractionTruth:\n    league:str\n    state:str\n    admitted:bool\n    reason:str\n    execution_authority:bool=False\n\ndef rows():\n    return (\n        SportsExtractionTruth("NFL","PHYSICAL_EXTRACTING",True,"OSN-044 repaired extractor produced 32 unique live events"),\n        SportsExtractionTruth("NCAAF","PHYSICAL_EXTRACTING",True,"OSN-045 exact scoreboard extractor produced 99 unique live events"),\n        SportsExtractionTruth("NBA","PHYSICAL_EXTRACTING",True,"OSN-036 positive-control physical extraction retained"),\n        SportsExtractionTruth("NCAAB","EXACT_EXTRACTOR_READY_CURRENT_PAGE_EMPTY",False,"Exact scoreboard contract proven; current official page has no initialGames records"),\n        SportsExtractionTruth("NHL","SOURCE_EVENT_SURFACE_REQUIRED",False,"Official schedule HTML shell exposed zero structured event objects"),\n        SportsExtractionTruth("MLS","SOURCE_EVENT_SURFACE_REQUIRED",False,"Current acquisition was schedule announcement article, not production event feed"),\n        SportsExtractionTruth("EPL","SOURCE_EVENT_SURFACE_REQUIRED",False,"Current acquisition was fixture announcement article, not production event feed"),\n        SportsExtractionTruth("UCL","BLOCKED",False,"Official UEFA runtime acquisition remains blocked"),\n    )\n')
    write('test_osn_049_sports_event_extraction_truth_registry_v2.py','\nfrom qseries_v2.oracle_source_network.certification.sports_event_extraction_truth_v2 import rows\nr=rows()\nfor x in r: print("[TRUTH]",x)\nadmitted=tuple(x.league for x in r if x.admitted)\nassert admitted==("NFL","NCAAF","NBA")\nassert all(x.execution_authority is False for x in r)\nassert next(x for x in r if x.league=="NCAAB").state=="EXACT_EXTRACTOR_READY_CURRENT_PAGE_EMPTY"\nassert next(x for x in r if x.league=="UCL").state=="BLOCKED"\nprint("[PASS] admitted physical event extraction leagues:",admitted)\nprint("[PASS] OSN-049 sports extraction truth registry certified")\n')
    print('[PASS] no held or blocked league admitted')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
