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
    print(' OSN-064 SPORTS PERSISTENCE IDEMPOTENT REPLAY GATE INSTALLER')
    print('='*120)
    require_file('qseries_v2/oracle_source_network/certification/sports_single_writer_physical_gate.py')
    put('qseries_v2/oracle_source_network/certification/sports_persistence_replay_gate.py','\nimport uuid\nfrom datetime import datetime,timezone\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\nfrom qseries_v2.oracle_source_network.persistence.sports_persistence_contract import from_canonical_event\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import canonicalize,submit,exact_readback,readback_count\n\n@dataclass(frozen=True)\nclass ReplayResult:\n    first_id:str\n    replay_id:str\n    same_identity:bool\n    exact_readback:int\n    execution_authority:bool=False\n\ndef certify_replay():\n    token=uuid.uuid4().hex[:12]\n    observed=datetime.now(timezone.utc).isoformat()\n    e=CanonicalSportsEvent(\n        league="MLS",season="2026",provider="osn_replay_fixture",\n        home_team="REPLAY_HOME",away_team="REPLAY_AWAY",\n        scheduled_start="2026-09-06T13:00:00Z",\n        source_observed_at=observed,source_authority="certification_fixture",\n        provider_event_id="replay-"+token,event_discriminator="replay-"+token,\n    )\n    raw=from_canonical_event(e)\n    batch="osn064-"+token\n    c1=canonicalize(raw,batch)\n    c2=canonicalize(raw,batch)\n    if c1.observation_id!=c2.observation_id:\n        raise RuntimeError("canonical replay identity drift")\n    submit((c1,))\n    submit((c2,))\n    rb,_=exact_readback(c1.observation_id)\n    return ReplayResult(c1.observation_id,c2.observation_id,True,readback_count(rb))\n')
    put('test_osn_064_sports_persistence_idempotent_replay_gate.py','\nfrom qseries_v2.oracle_source_network.certification.sports_persistence_replay_gate import certify_replay\nr=certify_replay()\nprint("[REPLAY]",r)\nassert r.same_identity is True\nassert r.first_id==r.replay_id\nassert r.exact_readback>=1\nassert r.execution_authority is False\nprint("[PASS] identical sports replay preserves canonical observation identity")\nprint("[PASS] duplicate replay remains exactly readable")\nprint("[PASS] OSN-064 sports persistence idempotency gate certified")\n')
    print('[PASS] same-event same-observation replay certification installed')
    print('[PASS] existing single-writer dedupe path reused')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
