from pathlib import Path

ROOT=Path.cwd()

def require(rel):
    p=ROOT/rel
    if not p.exists(): raise SystemExit('[FAIL] missing dependency: '+str(p))
    print('[PASS] dependency verified:',p.relative_to(ROOT))

def put(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content.rstrip()+'\n',encoding='utf-8')
    print('[WRITE]',p.relative_to(ROOT))

def main():
    print('='*118)
    print(' OSN-058 CROSS-LEAGUE CANONICAL EVENT INTEGRITY GATE INSTALLER')
    print('='*118)
    require('qseries_v2/oracle_source_network/canonical/sports_event_v2.py')
    put('qseries_v2/oracle_source_network/certification/cross_league_canonical_integrity.py','\nfrom dataclasses import dataclass\n\nREQUIRED=("league","season","provider","home_team","away_team","scheduled_start","source_observed_at","source_authority")\n\n@dataclass(frozen=True)\nclass IntegrityResult:\n    passed:bool\n    checked:int\n    failures:tuple\n    execution_authority:bool=False\n\ndef validate(events):\n    failures=[]\n    seen=set()\n    for i,e in enumerate(events):\n        for field in REQUIRED:\n            if not getattr(e,field,None):\n                failures.append((i,"missing",field))\n        cid=getattr(e,"canonical_event_id",None)\n        if not cid:\n            failures.append((i,"missing","canonical_event_id"))\n        elif cid in seen:\n            failures.append((i,"duplicate","canonical_event_id"))\n        else:\n            seen.add(cid)\n        if getattr(e,"execution_authority",None) is not False:\n            failures.append((i,"invalid","execution_authority"))\n        if getattr(e,"read_only",None) is not True:\n            failures.append((i,"invalid","read_only"))\n    return IntegrityResult(not failures,len(tuple(events)),tuple(failures))\n')
    put('test_osn_058_cross_league_canonical_event_integrity_gate.py','\nfrom qseries_v2.oracle_source_network.certification.cross_league_canonical_integrity import validate\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\n\nevents=[\n CanonicalSportsEvent(league="NFL",season="2026",provider="test",home_team="A",away_team="B",scheduled_start="2026-09-01T00:00:00Z",source_observed_at="2026-09-01T00:00:01Z",source_authority="official_league",provider_event_id="1",event_discriminator="1"),\n CanonicalSportsEvent(league="MLS",season="2026",provider="test",home_team="C",away_team="D",scheduled_start="2026-09-01T01:00:00Z",source_observed_at="2026-09-01T00:00:01Z",source_authority="official_league",provider_event_id="2",event_discriminator="2"),\n]\nr=validate(events)\nprint("[INTEGRITY]",r)\nassert r.passed and r.checked==2 and not r.failures\nassert r.execution_authority is False\nprint("[PASS] OSN-058 cross-league canonical integrity gate certified")\n')
    print('[PASS] canonical required-field validation installed')
    print('[PASS] duplicate canonical identity rejection installed')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
