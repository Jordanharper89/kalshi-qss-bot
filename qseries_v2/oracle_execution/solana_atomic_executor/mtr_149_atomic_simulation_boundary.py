
"""MTR-149: prove the canonical simulator's call boundary from local AST."""
import ast, json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'runtime_state/oracle/oracle_live_execution/mtr_149_atomic_simulation_boundary.json'
SOURCES={
 'runtime':'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py',
 'preflight':'mtr_119_canonical_alt_atomic_preflight.py',
 'gate':'qseries_v2/oracle_execution/solana_atomic_executor/mtr_147_protected_economics_gate.py'
}
TARGETS={'runtime':('simulate_current',),'preflight':('AtomicPreflight',),'gate':('ProtectedCandidateGate',)}
DANGER=('signed_tx','sign_transaction','keypair','private_key','send_transaction','send_raw_transaction','broadcast','ATOMIC.submit')

def dotted(node):
    result=[]
    while isinstance(node,ast.Attribute):
        result.insert(0,node.attr)
        node=node.value
    if isinstance(node,ast.Name): result.insert(0,node.id)
    return '.'.join(result)

def inspect_file(path,targets):
    raw=path.read_bytes()
    tree=ast.parse(raw.decode('utf-8-sig',errors='replace'),filename=path.name)
    found=[]
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and node.name in targets:
            calls=sorted({dotted(n.func) for n in ast.walk(node) if isinstance(n,ast.Call)})
            calls=[x for x in calls if x]
            args=[] if isinstance(node,ast.ClassDef) else [a.arg for a in node.args.posonlyargs+node.args.args+node.args.kwonlyargs]
            danger=sorted({x for x in calls if any(k.lower() in x.lower() for k in DANGER)})
            found.append({'name':node.name,'type':type(node).__name__,'line':node.lineno,
              'args':args,'calls':calls[:120],'dangerous_calls':danger,
              'return_count':sum(isinstance(x,ast.Return) for x in ast.walk(node))})
    return {'sha256':hashlib.sha256(raw).hexdigest(),'targets':found}

def run():
    report={'mtr':'MTR-149','mode':'SOURCE_BOUNDARY_ONLY','sources':{},'missing':[],
      'direct_simulation_approved':False,'official_verifier_connected':False,
      'atomic_two_leg_proof_closed':False,'production_cutover':False,
      'private_key_used':False,'signing':False,'broadcast':False,'scanner_modified':False}
    for key,rel in SOURCES.items():
        p=ROOT/rel
        if not p.is_file():
            report['missing'].append(rel);continue
        try: report['sources'][key]=inspect_file(p,TARGETS[key])
        except (OSError,SyntaxError,UnicodeError) as e: report['missing'].append(rel+':'+type(e).__name__)
        if key in report['sources'] and not report['sources'][key]['targets']:
            report['missing'].append(rel+':missing target')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    for key,data in report['sources'].items():
        for f in data['targets']:
            print('[MTR149_TARGET]',key,f['name'],'line',f['line'],'args',','.join(f['args']))
            print('[MTR149_CALLS]',key,','.join(f['calls']))
            print('[MTR149_SIGNER_RISKS]',key,','.join(f['dangerous_calls']) or 'NONE_DETECTED_IN_TARGET')
    print('[MTR149_MISSING]',report['missing'])
    print('[DIRECT_SIMULATION_APPROVED] FALSE')
    print('[OFFICIAL_VERIFIER_CONNECTED] FALSE')
    print('[ATOMIC_TWO_LEG_PROOF_CLOSED] FALSE')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')
    print('[REPORT]',OUT)
    if report['missing']:raise SystemExit('[HOLD] Canonical source contract missing')
    return report
if __name__=='__main__':run()
