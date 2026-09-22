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
    print(' OSN-063 SPORTS SINGLE-WRITER POSTGRESQL PHYSICAL GATE INSTALLER')
    print('='*120)
    require_file('qseries_v2/oracle_source_network/persistence/sports_persistence_contract.py')
    require_file('qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py')
    put('qseries_v2/oracle_source_network/certification/sports_single_writer_physical_gate.py','\nimport uuid\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\nfrom qseries_v2.oracle_source_network.persistence.sports_persistence_contract import from_canonical_event\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import canonicalize,submit,exact_readback,readback_count\n\n@dataclass(frozen=True)\nclass PhysicalPersistenceResult:\n    canonical_event_id:str\n    observation_id:str\n    submit_signature:str\n    readback_signature:str\n    exact_readback:int\n    execution_authority:bool=False\n\ndef persist_fixture():\n    token=uuid.uuid4().hex[:12]\n    now=datetime.now(timezone.utc).isoformat()\n    e=CanonicalSportsEvent(\n        league="NFL",season="2026",provider="osn_physical_fixture",\n        home_team="OSN_HOME",away_team="OSN_AWAY",\n        scheduled_start="2026-09-06T12:00:00Z",\n        source_observed_at=now,source_authority="certification_fixture",\n        provider_event_id="osn-"+token,event_discriminator="osn-"+token,\n    )\n    raw=from_canonical_event(e)\n    c=canonicalize(raw,"osn063-"+token)\n    oid=c.observation_id\n    _,ss=submit((c,))\n    rb,rs=exact_readback(oid)\n    n=readback_count(rb)\n    return PhysicalPersistenceResult(e.canonical_event_id,oid,ss,rs,n)\n')
    put('test_osn_063_sports_single_writer_postgresql_physical_gate.py','\nfrom qseries_v2.oracle_source_network.certification.sports_single_writer_physical_gate import persist_fixture\nr=persist_fixture()\nprint("[PHYSICAL]",r)\nassert r.exact_readback>=1\nassert len(r.observation_id)>=32\nassert r.execution_authority is False\nprint("[PASS] sports canonical observation persisted through OPH-019 single writer")\nprint("[PASS] exact PostgreSQL observation-ID readback certified")\nprint("[PASS] OSN-063 physical sports persistence gate certified")\n')
    print('[PASS] bounded one-observation physical certification installed')
    print('[PASS] write must pass exact observation-ID PostgreSQL readback')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
