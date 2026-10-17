"""ORACLE-369: safe native-provider discovery and conditional binding.
One full installer; Windows CMD; no key, signing, broadcast, or provider RPC in audit.
Does not claim native capability unless an existing local provider implements
prepare_unsigned(candidate) and explicitly declares execution firewalls.
"""
from __future__ import annotations
import argparse, ast, hashlib, importlib, inspect, json, os, py_compile, re, sys, tempfile, unittest
from pathlib import Path

PKG='qseries_v2.oracle_execution.solana_atomic_executor'
ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET=ROOT/'oracle_369_native_provider_binding.py'
REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_369_native_provider_binding_report.json')
PROVIDER=ROOT/'oracle_366_native_atomic_provider.py'
MAX_SOURCE=1_000_000
SYMBOLS=('prepare_unsigned','compile_current','signed_tx','native_instructions','atomic','build_swap','quote','pump','meteora','alt')

def atomic_write(path, payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False,mode='wb') as h:
        h.write(payload); tmp=Path(h.name)
    os.replace(tmp,path)

def install():
    ROOT.mkdir(parents=True,exist_ok=True)
    source=Path(__file__).resolve().read_bytes()
    compile(source.decode('utf-8'),str(TARGET),'exec')
    if Path(__file__).resolve()!=TARGET.resolve():atomic_write(TARGET,source)
    py_compile.compile(str(TARGET),doraise=True)
    assert TARGET.read_bytes()==source
    print('[ORACLE369_INSTALL_PASS]',str(TARGET),'sha256='+hashlib.sha256(source).hexdigest())

def declaration(tree,key):
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for lhs in node.targets:
                if isinstance(lhs,ast.Name) and lhs.id==key:
                    return isinstance(node.value,ast.Constant) and node.value.value is False
        if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id==key:
            return isinstance(node.value,ast.Constant) and node.value.value is False
    return False

def discover(root=ROOT):
    candidates=[]
    if not root.exists():return candidates
    for path in sorted(root.glob('*.py')):
        if path.name.startswith('oracle_369_') or path.stat().st_size>MAX_SOURCE:continue
        try:tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        except (SyntaxError,UnicodeError,OSError):continue
        funcs=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        names={n.name for n in funcs}
        match=[s for s in SYMBOLS if any(s in n.lower() for n in names)]
        contract=next((n for n in funcs if n.name=='prepare_unsigned'),None)
        exact_contract=bool(contract and not isinstance(contract,ast.AsyncFunctionDef) and len(contract.args.posonlyargs)==0 and len(contract.args.args)==1 and not contract.args.vararg and not contract.args.kwarg and not contract.args.kwonlyargs)
        if match or contract:
            candidates.append({'module':path.stem,'path':str(path),'matches':match[:8],
                'prepare_unsigned':bool(contract),'prepare_signature_compatible':exact_contract,
                'execution_authority_false':declaration(tree,'EXECUTION_AUTHORITY'),
                'broadcast_false':declaration(tree,'BROADCAST'),
                'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    return candidates

def eligible(rows):
    return [r for r in rows if r['prepare_signature_compatible'] and r['execution_authority_false'] and r['broadcast_false']]

def inspect_repo(root=ROOT):
    rows=discover(root); matches=eligible(rows)
    # Audit rather than execute arbitrary builder code. Only a unique compatible module
    # may be selected; passing its runtime proof still requires ORACLE-368 checks.
    status='ONE_STATIC_PROVIDER_CANDIDATE' if len(matches)==1 else 'AMBIGUOUS_PROVIDER_HOLD' if len(matches)>1 else 'NO_NATIVE_PROVIDER_CONTRACT'
    return {'status':status,'compatible_provider_modules':[r['module'] for r in matches],
        'native_candidates':[r for r in rows if r['matches'] or r['prepare_unsigned']],
        'native_provider_bound':False,'private_key_used':False,'signing':False,'broadcast':False,
        'canary_lamports':10000000}

def upstream_audit():
    m=importlib.import_module(PKG+'.oracle_368_source_boundary_repair')
    m.audit()
    return m

def audit():
    upstream_audit()
    assert TARGET.is_file() and TARGET.read_bytes()==Path(__file__).resolve().read_bytes(),'INSTALL_INTEGRITY'
    rows=discover()
    report=inspect_repo()
    atomic_write(REPORT,json.dumps(report,sort_keys=True,indent=2).encode('utf-8'))
    print('[ORACLE369_AUDIT_PASS]',json.dumps({'status':report['status'],'eligible':report['compatible_provider_modules'],
        'native_source_modules':len(rows),'report':str(REPORT),'no_key_no_sign_no_broadcast':True}))
    return report

def run(seconds=90,poll_ms=5,ttl_ms=2500,max_age_ms=1500):
    data=audit()
    if len(data['compatible_provider_modules'])!=1:
        print('[ORACLE369_NATIVE_PROVIDER_HOLD]',json.dumps({'reason':data['status'],
            'next':'NATIVE_BUILDER_CONTRACT_REQUIRED','report':str(REPORT),'execution_authority':False}))
        return 0
    # A matching function name and two constants are NOT proof that the native
    # implementation cannot sign or send. A separately code-reviewed adapter is
    # required before this boundary is enabled. Do not import arbitrary modules.
    print('[ORACLE369_NATIVE_PROVIDER_HOLD]',json.dumps({
        'reason':'MATCHING_SIGNATURE_NOT_YET_CODE_REVIEWED',
        'module':data['compatible_provider_modules'][0],
        'next':'VERIFY_NATIVE_PUMP_DLMM_BUILDER_AND_BANK_PROOF',
        'signing':False,'broadcast':False,'execution_authority':False}))
    return 0

def tests():
    class Test(unittest.TestCase):
        def test_firewall_true_rejected(self):
            t=ast.parse('EXECUTION_AUTHORITY=True\nBROADCAST=False\ndef prepare_unsigned(candidate): return {}')
            self.assertFalse(declaration(t,'EXECUTION_AUTHORITY'))
        def test_firewall_false(self):
            t=ast.parse('EXECUTION_AUTHORITY=False\nBROADCAST=False')
            self.assertTrue(declaration(t,'EXECUTION_AUTHORITY'))
        def test_discovery(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d); (p/'native.py').write_text('EXECUTION_AUTHORITY=False\nBROADCAST=False\ndef prepare_unsigned(candidate): return {}')
                r=discover(p);self.assertEqual(len(eligible(r)),1)
        def test_ambiguous(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)
                for n in ('a','b'):(p/(n+'.py')).write_text('EXECUTION_AUTHORITY=False\nBROADCAST=False\ndef prepare_unsigned(candidate): return {}')
                self.assertEqual(inspect_repo(p)['status'],'AMBIGUOUS_PROVIDER_HOLD')
        def test_empty(self):
            with tempfile.TemporaryDirectory() as d:self.assertEqual(inspect_repo(Path(d))['status'],'NO_NATIVE_PROVIDER_CONTRACT')
        def test_fake_argument(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);(p/'native.py').write_text('EXECUTION_AUTHORITY=False\nBROADCAST=False\ndef prepare_unsigned(x,y): pass')
                self.assertFalse(eligible(discover(p)))
        def test_does_not_access_key(self):
            self.assertNotIn('getenv(\'QSB_SOLANA_PRIVATE_KEY\')',inspect.getsource(run))
        def test_canary(self):self.assertEqual(inspect_repo(Path('/not_existing_369_path'))['canary_lamports'],10000000)
    res=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Test))
    print('[ORACLE369_TEST_PASS]' if res.wasSuccessful() else '[ORACLE369_TEST_FAIL]',res.testsRun)
    return res.wasSuccessful()

def main():
    parser=argparse.ArgumentParser()
    for flag in ('install','test','audit','run'):parser.add_argument('--'+flag,action='store_true')
    parser.add_argument('--seconds',type=int,default=90);parser.add_argument('--poll-ms',type=int,default=5)
    parser.add_argument('--ttl-ms',type=int,default=2500);parser.add_argument('--max-age-ms',type=int,default=1500)
    x=parser.parse_args()
    if not any((x.install,x.test,x.audit,x.run)):parser.error('SELECT_ACTION')
    if x.install:install()
    if x.test and not tests():return 1
    if x.audit:audit()
    if x.run:return run(x.seconds,x.poll_ms,x.ttl_ms,x.max_age_ms)
    return 0
if __name__=='__main__':raise SystemExit(main())
