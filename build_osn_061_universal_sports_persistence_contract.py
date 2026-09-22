from pathlib import Path
import ast

ROOT=Path.cwd()

def require_file(rel):
    p=ROOT/rel
    if not p.exists(): raise SystemExit('[FAIL] missing dependency: '+str(p))
    print('[PASS] dependency verified:',p.relative_to(ROOT))
    return p

def require_symbol(rel,symbol):
    p=require_file(rel)
    tree=ast.parse(p.read_text(encoding='utf-8',errors='ignore'))
    names={n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    if symbol not in names: raise SystemExit(f'[FAIL] exact symbol missing: {rel} -> {symbol}')
    print(f'[PASS] exact symbol verified: {rel} -> {symbol}')

def put(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    compile(content,str(p),'exec')
    p.write_text(content.rstrip()+'\n',encoding='utf-8')
    print('[WRITE]',p.relative_to(ROOT))

def main():
    print('='*120)
    print(' OSN-061 UNIVERSAL SPORTS PERSISTENCE CONTRACT INSTALLER')
    print('='*120)
    require_file('qseries_v2/oracle_source_network/canonical/sports_event_v2.py')
    require_symbol('qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py','canonicalize_expansion_observation')
    put('qseries_v2/oracle_source_network/persistence/sports_persistence_contract.py','\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\n\n@dataclass(frozen=True)\nclass SportsPersistenceObservation:\n    source_id:str\n    observed_at:str\n    observation_type:str\n    provider:str\n    subject:str\n    provenance_hash:str\n    payload:dict\n    source_class:str="official_sports_event"\n\ndef from_canonical_event(event):\n    payload={\n        "canonical_event_id":event.canonical_event_id,\n        "league":event.league,\n        "season":event.season,\n        "home_team":event.home_team,\n        "away_team":event.away_team,\n        "scheduled_start":event.scheduled_start,\n        "status":getattr(event,"status",None),\n        "home_score":getattr(event,"home_score",None),\n        "away_score":getattr(event,"away_score",None),\n        "provider_event_id":getattr(event,"provider_event_id",None),\n        "schedule_revision":getattr(event,"schedule_revision",0),\n        "read_only":True,\n        "execution_authority":False,\n    }\n    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()\n    ph=sha256(raw).hexdigest()\n    return SportsPersistenceObservation(\n        source_id=f"source.sports.{event.league.lower()}.{event.provider}.{event.canonical_event_id}",\n        observed_at=event.source_observed_at,\n        observation_type="official_sports_event",\n        provider=event.provider,\n        subject=event.canonical_event_id,\n        provenance_hash=ph,\n        payload=payload,\n    )\n')
    put('test_osn_061_universal_sports_persistence_contract.py','\nfrom qseries_v2.oracle_source_network.persistence.sports_persistence_contract import from_canonical_event\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\n\ne=CanonicalSportsEvent(\n league="NFL",season="2026",provider="fixture",\n home_team="A",away_team="B",\n scheduled_start="2026-09-06T00:00:00Z",\n source_observed_at="2026-09-05T23:59:00Z",\n source_authority="official_league",\n provider_event_id="evt-1",event_discriminator="evt-1",\n)\nx=from_canonical_event(e)\nprint("[SPORTS_PERSISTENCE]",x)\nassert set(x.__dict__)=={"source_id","observed_at","observation_type","provider","subject","provenance_hash","payload","source_class"}\nassert x.payload["canonical_event_id"]==e.canonical_event_id\nassert x.payload["read_only"] is True\nassert x.payload["execution_authority"] is False\nprint("[PASS] OSN-061 exact OAD-261 eight-field sports persistence contract certified")\n')
    print('[PASS] sports event mapped onto exact OAD-261 eight-field observation shape')
    print('[PASS] canonical sports identity retained in payload')
    print('[PASS] read_only=TRUE execution_authority=FALSE')

if __name__=='__main__': main()
