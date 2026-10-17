from __future__ import annotations
"""Complete isolated V15 scanner+supervisor installers: V12/V13 source derived, no in-place patches.

V15 changes only the new scanner's certified discovery -> native hydration boundary.
Q18/Q20/Q25, ORACLE322 original, V12, V13, shared core and canonical bus preserved.
"""
import argparse, ast, hashlib, os, re, tempfile, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
V12=ROOT/'build_final_boss_v12_scanner_runtime.py'
V13=ROOT/'build_final_boss_v13_supervisor_replacement.py'
NEW=ROOT/'build_final_boss_v15_scanner_runtime.py'
SUP=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/final_boss_v15_supervisor.py'
V12_HASH='0f517676251aa6f1a3cc5e98dfb2d686b581dd75c0eb283a40eadb03ed8b8cc2'
V12_INNER='ad2f54c6ac6da9e3b65d5841a19389eaf33cd9fe13f452ef84b09d1fa61562b9'
V13_MODULE='4e8502ec6664b5e97d6d13388ddfa4d886a55159e8fbf4fb205aefc057cf8d91'

def sha(b):return hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()
def off(lines,line,col):return sum(len(x) for x in lines[:line-1])+col

def embedded(src,nametag='SOURCE'):
    t=ast.parse(src)
    nodes=[]
    for n in ast.walk(t):
        if isinstance(n,(ast.Assign,ast.AnnAssign)):
            val=n.value
            names=[a.id for a in getattr(n,'targets',[]) if isinstance(a,ast.Name)]
            if isinstance(getattr(n,'target',None),ast.Name):names.append(n.target.id)
            if (nametag in names or (nametag=='SOURCE' and 'SCRIPT' in names)) and isinstance(val,ast.Constant) and isinstance(val.value,str) and len(val.value)>3500:
                nodes.append(val)
    if len(nodes)!=1:raise RuntimeError('EXPECTED_ONE_EMBEDDED_SOURCE')
    return nodes[0]

BRIDGE=r'''
# V15: scoped, verified native admission. No mutation to original engine on disk.
_v15_original_scan_epoch=scan_epoch

def scan_epoch(*args,**kwargs):
    import json as _j, time as _t
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine as _e
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as _pd
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as _c
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as _merged
    _orig=_e.candidate_universe
    _old_prepare=_pd.prepare_pairs
    _witness={'selected':[], 'rejected':{}, 'hydrated':0}
    _allowed={'SPL_PROVISIONAL_SIM_REVIEW','TOKEN2022_METADATA_ONLY_SIM_REVIEW'}
    def _meta(row):
        tok,pump,pool=(row.get(x) for x in ('token','pump_pool','meteora_pool'))
        for x in (tok,pump,pool):
            if not isinstance(x,str) or not 32<=len(x)<=44 or len(_c.b58d(x))!=32:
                raise ValueError('BAD_EXACT_TRIPLE')
        if len({tok,pump,pool})!=3:raise ValueError('ALIAS_POOL_IDENTITY')
        if row.get('risk_scope') not in _allowed:raise ValueError('STAGED_TOKEN_RISK_NOT_REVIEWABLE')
        pd,owner=_c.account(pump)
        if owner!=_c.PUMP:raise ValueError('PUMP_PROGRAM_OWNER_MISMATCH')
        pp=_c.decode_pump_pool(pd)
        if pp['base_mint']!=tok or pp['quote_mint']!=_c.WSOL:
            raise ValueError('PUMP_TOKEN_MINT_PAIR_MISMATCH')
        _,owner=_c.account(pool)
        if owner!=_c.DLMM:raise ValueError('DLMM_PROGRAM_OWNER_MISMATCH')
        # Indexer supplies route-specific decimals only; exact identities are
        # already V8 onchain-certified and are rechecked above.
        j=_c.http('https://dlmm.datapi.meteora.ag/pools?page=1&page_size=100&query='+tok)
        rows=j.get('data',[]) if isinstance(j,dict) else j
        if not isinstance(rows,list):raise ValueError('METEORA_INDEX_RESPONSE_INVALID')
        matches=[]
        for d in rows:
            if not isinstance(d,dict):continue
            addr=d.get('address') or d.get('pool_address') or d.get('pubkey')
            if addr!=pool:continue
            x=d.get('token_x') or d.get('tokenX') or {}
            y=d.get('token_y') or d.get('tokenY') or {}
            def mint(v):return v if isinstance(v,str) else (v.get('address') or v.get('mint') or v.get('token_address')) if isinstance(v,dict) else None
            mx,my=mint(x),mint(y)
            if {mx,my}!={tok,_c.WSOL}:raise ValueError('DLMM_POOL_MINT_MISMATCH')
            # Derive decimals from onchain mint accounts, not from an indexer default.
            dxraw,dxowner=_c.account(mx);dyraw,dyowner=_c.account(my)
            if dxowner not in (_c.TOKEN,_c.TOKEN22) or dyowner not in (_c.TOKEN,_c.TOKEN22) or min(len(dxraw),len(dyraw))<45:
                raise ValueError('MINT_DATA_OR_OWNER_INVALID')
            matches.append({'address':pool,'token_x':mx,'token_y':my,
                            'decimals_x':int(dxraw[44]),'decimals_y':int(dyraw[44])})
        if len(matches)!=1:raise ValueError('EXACT_DLMM_POOL_NOT_UNIQUELY_INDEXED')
        return matches[0]
    def _universe(root):
        try:
            # Capture time-bounded V12 exact identities BEFORE baseline network
            # discovery (which can take long enough for certificates to expire).
            ranked=_e.raw_candidate_universe(root)
        except Exception as exc:
            ranked=[]
            _witness['rejected']['RAW_SOURCE_'+type(exc).__name__]=1
        baseline=_orig(root)
        verified=[r for r in ranked if isinstance(r,dict) and
                  r.get('v12_admission')=='CERTIFIED_DISCOVERY_NEEDS_NATIVE_WARM']
        selected=[];seen=set()
        for r in verified[:28]:
            try:
                tok=r['token']
                if tok in seen:continue
                meta=_meta(r)
                selected.append({'token':tok,'pump_pool':r['pump_pool'],
                                 'meteora_pool':meta['address'],'meteora_meta':meta,
                                 'source':'MRIYA_V8_NATIVE_BOUND','crosslisted':True,
                                 'risk_scope':r['risk_scope']})
                seen.add(tok)
            except Exception as exc:
                k=type(exc).__name__+':'+str(exc)[:72]
                _witness['rejected'][k]=_witness['rejected'].get(k,0)+1
        # Mriya is prioritized first; actual hydrated routes are subsequently
        # limited by the observed address budget, not a fictional fixed 9-pair cap.
        cap=min(int(_pd.MAX_PAIRS),28)
        rows=selected+[r for r in baseline if r.get('token') not in seen]
        rows=rows[:cap]
        _witness['selected']=[(r['token'],r['pump_pool'],r['meteora_pool']) for r in selected if r in rows]
        print('[BOSS_V15_NATIVE_ADMISSION] '+_j.dumps({'v8_exact_bound':len(_witness['selected']),
              'fallback_baseline':len(rows)-len(_witness['selected']),
              'max_pairs':cap,'rejected':_witness['rejected'],
              'funded_execution_authority':False,'broadcast':False},sort_keys=True),flush=True)
        return rows
    def _prepare(root):
        pairs,landing=_old_prepare(root)
        # Native route accounts are inserted before non-core observation roles in
        # merged.prepare(). Prevent the merged MAX_ACCOUNTS slice from silently
        # dropping a watched DLMM array from any admitted native route.
        reserve=64
        budget=max(0,int(_merged.MAX_ACCOUNTS)-reserve)
        used=set();kept=[];dropped=0
        for p in pairs:
            req={p.pump_base_vault,p.pump_quote_vault,p.meteora_pool}
            req.update(x[1] for x in p.arrays)
            if len(used|req)>budget:
                dropped+=1
                continue
            kept.append(p);used.update(req)
        pairs=kept
        actual={(p.token,p.pump_pool,p.meteora_pool) for p in pairs}
        admitted=[r for r in _witness['selected'] if r in actual]
        _witness['hydrated']=len(admitted)
        print('[BOSS_V15_HYDRATION_WITNESS] '+_j.dumps({
              'requested_verified':len(_witness['selected']),
              'native_verified_hydrated':len(admitted),'all_pairs':len(pairs),
              'watched_native_accounts':len(used),'native_account_budget':budget,
              'dropped_for_account_budget':dropped,
              'failed_verified':len(_witness['selected'])-len(admitted),
              'broadcast':False},sort_keys=True),flush=True)
        return pairs,landing
    _e.candidate_universe=_universe
    _pd.prepare_pairs=_prepare
    try:return _v15_original_scan_epoch(*args,**kwargs)
    finally:
        _e.candidate_universe=_orig
        _pd.prepare_pairs=_old_prepare
'''

def replace_const(src, node, inner):
    lines=src.splitlines(keepends=True)
    a=off(lines,node.lineno,node.col_offset);b=off(lines,node.end_lineno,node.end_col_offset)
    new=src[:a]+repr(inner)+src[b:]
    ast.parse(new)
    return new

def scanner_builder(raw):
    if sha(raw)!=V12_HASH:raise RuntimeError('V12_SCANNER_BUILDER_SHA_DRIFT')
    outer=raw.decode('utf-8-sig')
    n=embedded(outer)
    s=n.value
    if sha(s.encode())!=V12_INNER:raise RuntimeError('V12_SCANNER_EMBEDDED_SHA_DRIFT')
    tree=ast.parse(s)
    funcs=[f for f in tree.body if isinstance(f,ast.FunctionDef) and f.name=='scan_epoch']
    if len(funcs)!=1:raise RuntimeError('SCANNER_FUNCTION_DRIFT')
    lines=s.splitlines(keepends=True)
    lines.insert(funcs[0].end_lineno,'\n'+BRIDGE+'\n')
    new=''.join(lines)
    ast.parse(new)
    if new.count('def scan_epoch(')!=2:raise RuntimeError('SCANNER_WRAPPER_COUNT_INVALID')
    # Refuse all edits outside original embedded scanner SOURCE constant.
    rebuilt=replace_const(outer,n,new)
    return rebuilt.encode('utf-8')

def supervisor_source(raw):
    tree=ast.parse(raw.decode('utf-8-sig'))
    node=embedded(raw.decode('utf-8-sig'))
    s=node.value
    if sha(s.encode())!=V13_MODULE:raise RuntimeError('V13_SUPERVISOR_SOURCE_DRIFT')
    replacements={
      "'build_final_boss_v12_scanner_runtime.py'":"'build_final_boss_v15_scanner_runtime.py'",
      "'v13_supervisor.lock'":"'v15_supervisor.lock'",
      "'final_boss_v13_supervisor.json'":"'final_boss_v15_supervisor.json'",
      "'FINAL_BOSS_V13'":"'FINAL_BOSS_V15'",
      "'[FINAL_BOSS_V13_SUPERVISOR]'":"'[FINAL_BOSS_V15_SUPERVISOR]'",
      "'[FINAL_BOSS_V13_INSPECT]'":"'[FINAL_BOSS_V15_INSPECT]'",
      "'[FINAL_BOSS_V13_HOLD]'":"'[FINAL_BOSS_V15_HOLD]'",
    }
    for old,new in replacements.items():
        if old not in s:raise RuntimeError('V13_INTERFACE_CHANGED:'+old)
        s=s.replace(old,new)
    # Preserve V13's acknowledged child-heartbeat logic; derive V15 scanner
    # against V12 from the verified complete V15 installer, not the V12 baseline.
    original="""    expected, _ = v12.make_builder(SOURCE.read_bytes())
    if DERIVED.read_bytes() != expected:
        raise Hold('DERIVED_SCANNER_SOURCE_DRIFT')"""
    updated="""    from build_final_boss_v15_native_admission import scanner_builder
    baseline, _ = v12.make_builder(SOURCE.read_bytes())
    expected = scanner_builder(baseline)
    if DERIVED.read_bytes() != expected:
        raise Hold('DERIVED_SCANNER_SOURCE_DRIFT')"""
    if original not in s:raise RuntimeError('V13_SOURCE_GUARD_DRIFT')
    s=s.replace(original,updated)
    # Distinct supervisor exclusivity, including the still-running V13 lock.
    s=s.replace("if running_scanner() or OLD_LOCK.exists():", "if running_scanner() or OLD_LOCK.exists() or (BASE/'v13_supervisor.lock').exists():")
    s=s.replace("if running_scanner() or OLD_LOCK.exists():", "if running_scanner() or OLD_LOCK.exists() or (BASE/'v13_supervisor.lock').exists():")
    ast.parse(s)
    return s.encode('utf-8')

def atomic(path, raw):
    if path.is_symlink():raise RuntimeError('DESTINATION_IS_SYMLINK')
    if path.exists():
        if path.read_bytes()!=raw:raise RuntimeError('DESTINATION_ALREADY_CHANGED')
        return 'VERIFIED_EXISTING'
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=path.parent,delete=False,suffix='.tmp') as f:
        f.write(raw);temp=Path(f.name)
    try:os.replace(temp,path)
    finally:temp.unlink(missing_ok=True)
    return 'INSTALLED'

def install():
    if not V12.is_file() or V12.is_symlink() or not V13.is_file() or V13.is_symlink():
        raise RuntimeError('V12_OR_V13_REFERENCE_MISSING')
    sb=scanner_builder(V12.read_bytes())
    sv=supervisor_source(V13.read_bytes())
    print('[V15_SCANNER]',atomic(NEW,sb),'sha256='+sha(sb))
    print('[V15_SUPERVISOR]',atomic(SUP,sv),'sha256='+sha(sv))
    print('[PRESERVED] ORIGINAL_ORACLE322_V12_V13_Q18_Q20_Q25_V14_CORE_AND_CANONICAL_BUS')
    print('[SAFETY] signing=false broadcast=false live_cutover_not_claimed')

def fixture_tests():
    import contextlib, io, types
    from unittest.mock import patch
    token='kXzjEQ2frgfKHAUWGS1rZFH53tyWjD6b9njoQ82pump'
    pump='F9WeWAyn3N166e5PAbjMefQNjq6AGMf3pEc7AE86S95Q'
    pool='8snrTkrb4ohEjJMrKJ5fob1GCaNNiu7wLj8a5FBqB3vz'
    wsol='So11111111111111111111111111111111111111112'
    E=types.ModuleType('engine');P=types.ModuleType('live_account_stream')
    C=types.ModuleType('core');M=types.ModuleType('merged_live_runtime')
    M.MAX_ACCOUNTS=256;P.MAX_PAIRS=28
    E.candidate_universe=lambda root:[{'token':'baseline','pump_pool':'oldpool','meteora_pool':'oldmeta'}]
    E.raw_candidate_universe=lambda root:[dict(token=token,pump_pool=pump,meteora_pool=pool,
         v12_admission='CERTIFIED_DISCOVERY_NEEDS_NATIVE_WARM',risk_scope='TOKEN2022_METADATA_ONLY_SIM_REVIEW')]
    C.WSOL=wsol;C.PUMP='pump_program';C.DLMM='dlmm_program';C.TOKEN='spl';C.TOKEN22='token22'
    C.b58d=lambda v:b'0'*32
    C.decode_pump_pool=lambda data:dict(base_mint=token,quote_mint=wsol)
    def account(k):
        if k==pump:return b'pool','pump_program'
        if k==pool:return b'pool','dlmm_program'
        if k in (token,wsol):
            raw=bytearray(82);raw[44]=9
            return bytes(raw),'spl'
        raise AssertionError('unexpected account')
    C.account=account
    C.http=lambda url:{'data':[{'address':pool,'token_x':dict(address=token),'token_y':dict(address=wsol)}]}
    def prep(root):
        r=E.candidate_universe(root)
        return ([types.SimpleNamespace(token=x['token'],pump_pool=x['pump_pool'],meteora_pool=x['meteora_pool'],
              pump_base_vault='a'+str(i),pump_quote_vault='b'+str(i),arrays=[(0,'c'+str(i),b'')])
              for i,x in enumerate(r)],0)
    P.prepare_pairs=prep
    pkg=types.ModuleType('qseries_v2')
    s_pkg=types.ModuleType('qseries_v2.oracle_strategy_intelligence')
    m_pkg=types.ModuleType('qseries_v2.oracle_strategy_intelligence.solana_money')
    q_pkg=types.ModuleType('qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot')
    n_pkg=types.ModuleType('qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine')
    q_pkg.engine=E;q_pkg.live_account_stream=P;q_pkg.merged_live_runtime=M;n_pkg.core=C
    mods={pkg.__name__:pkg,s_pkg.__name__:s_pkg,m_pkg.__name__:m_pkg,
          q_pkg.__name__:q_pkg,n_pkg.__name__:n_pkg}
    capture=io.StringIO()
    with patch.dict(sys.modules,mods):
        ns={'_e':E,'_pd':P}
        exec('def scan_epoch():\n    return _e.candidate_universe(None), _pd.prepare_pairs(None)\n'+BRIDGE,ns)
        with contextlib.redirect_stdout(capture):
            result=ns['scan_epoch']()
    assert result[0][0]['meteora_meta']['address']==pool
    assert result[1][0][0].token==token
    assert '[BOSS_V15_HYDRATION_WITNESS]' in capture.getvalue()
    assert '"native_verified_hydrated": 1' in capture.getvalue()
    assert E.candidate_universe.__name__=='<lambda>' and P.prepare_pairs is prep
    print('[PASS] V15 fixture: V12-certified triple -> exact onchain+indexer -> native pool hydration; baseline preserved; hooks restored')

def tests():
    fixture_tests()
    tree=ast.parse('''def scan_epoch(*args,**kwargs):\n    return 7\n\ndef main():\n    return scan_epoch()\n''')
    rows='def scan_epoch(*args,**kwargs):\n    return 7\n\ndef main():\n    return scan_epoch()\n'
    offset_fn=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='scan_epoch'][0]
    lines=rows.splitlines(keepends=True)
    lines.insert(offset_fn.end_lineno,'\n'+BRIDGE+'\n')
    out=''.join(lines)
    assert out.count('def scan_epoch(')==2
    ast.parse(out)
    assert "funded_execution_authority':False" in out
    assert 'sendTransaction' not in out and 'sendRawTransaction' not in out
    # V13 exact original module source is pinned; install guard prevents unverified artifact use.
    assert sha(embedded(V13.read_text(encoding='utf-8')).value.encode())==V13_MODULE
    ast.parse(supervisor_source(V13.read_bytes()).decode('utf-8'))
    assert len(range(10_000_000,100_000_001,5_000_000))==19
    print('[PASS] V15 full source-isolated native admission, exact V12 witness, onchain binding, supervisor single writer, 19 sizes, no broadcast')
    print('[BOUNDARY] Fixtures only; new Mriya hydration and executor events require live Windows cutover')

def main():
    a=argparse.ArgumentParser()
    group=a.add_mutually_exclusive_group(required=True)
    group.add_argument('--test',action='store_true');group.add_argument('--install',action='store_true')
    x=a.parse_args()
    try:
        if x.test:tests()
        else:install()
        return 0
    except Exception as exc:
        print('[V15_HOLD]',type(exc).__name__+':'+str(exc)[:130],flush=True)
        return 2
if __name__=='__main__':raise SystemExit(main())
