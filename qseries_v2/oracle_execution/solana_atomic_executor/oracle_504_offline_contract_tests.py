from __future__ import annotations
"""Offline contract verification of ORACLE-504 targeted hydration, no network."""
import importlib.util,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def stub(name):
    x=types.ModuleType(name)
    if name not in sys.modules:sys.modules[name]=x
    return sys.modules[name]

def tests():
    prefix='qseries_v2'
    for n in ('qseries_v2','qseries_v2.oracle_strategy_intelligence',
              'qseries_v2.oracle_strategy_intelligence.solana_money',
              'qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine',
              'qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot'):
        p=stub(n);p.__path__=[]
        if '.' in n:
            owner,member=n.rsplit('.',1)
            setattr(sys.modules[owner],member,p)
    base='qseries_v2.oracle_strategy_intelligence.solana_money.'
    core=stub(base+'native_atomic_money_machine.core')
    core.WSOL='S'*44
    engine=stub(base+'qarb_clean_bot.engine')
    runtime=stub(base+'qarb_clean_bot.merged_live_runtime')
    rc=types.SimpleNamespace(discover=lambda root:['ORIGINAL'])
    runtime.rc=rc
    engine.candidate_universe=lambda root:['ORIGINAL']
    sys.modules[base+'native_atomic_money_machine'].core=core
    sys.modules[base+'qarb_clean_bot'].engine=engine
    sys.modules[base+'qarb_clean_bot'].merged_live_runtime=runtime
    spec=importlib.util.spec_from_file_location('oracle504_hydrated',ROOT/'oracle_504_targeted_native_hydration.py')
    hyd=importlib.util.module_from_spec(spec);spec.loader.exec_module(hyd)
    token,pump,dlmm,wallet=('3'*44,'4'*44,'5'*44,'6'*44)
    row={'token':token,'pump_pool':pump,'meteora_pool':dlmm}
    meta={'address':dlmm,'token_x':token,'token_y':core.WSOL,'decimals_x':6,'decimals_y':9}
    assert hyd.manifest(row,meta)['meteora_pool']==dlmm
    try:hyd.manifest(row,dict(meta,address='7'*44))
    except hyd.TargetHold as e:assert str(e)=='TARGET_DLMM_POOL_DIFFERS_FROM_SCANNER'
    else:raise AssertionError('mismatched pool accepted')
    old_universe=engine.candidate_universe
    old_discovery=runtime.rc.discover
    stage=[]
    pair=types.SimpleNamespace(token=token,pump_pool=pump,meteora_pool=dlmm)
    def orig_prepare(root):
        x=engine.candidate_universe(root)
        assert len(x)==1 and x[0]['pump_pool']==pump
        assert runtime.rc.discover(root)==[]
        stage.append('EXACT_STATE')
        return {'pairs':[pair]}
    def templates(state,owner):
        assert owner==wallet
        stage.append('PUMP_NATIVE')
    def meteora(state,owner,warmed):
        assert owner==wallet and warmed==[{'token':token,'program':'Token2022'}]
        stage.append('DLMM_NATIVE')
    q60b=types.SimpleNamespace(_ORIG_PREPARE=orig_prepare)
    q25=types.SimpleNamespace(q60b2=types.SimpleNamespace(q60b=q60b),
                               bind_cached_state=lambda s:stage.append('BOUND'))
    old=types.SimpleNamespace(q25=q25,
        install_proven_hot_math=lambda state:[{'token':token,'program':'Token2022'}],
        prebuild_templates=templates,prebuild_meteora_templates=meteora)
    fw=types.SimpleNamespace(wallet=wallet)
    prov=types.SimpleNamespace(old=old,forward=fw,refresh_attempts=0)
    ans=hyd.exact_native_refresh(prov,row,resolve_meta=lambda tok:meta)
    assert ans['warm_complete'] and not ans['reuse_triggering_nomination']
    assert fw.pairs[token] is pair and fw.indexes[token]==0
    assert stage==['EXACT_STATE','BOUND','PUMP_NATIVE','DLMM_NATIVE']
    assert engine.candidate_universe is old_universe and runtime.rc.discover is old_discovery
    stage.clear()
    try:hyd.exact_native_refresh(prov,row,resolve_meta=lambda tok:meta,
                                 build_state=lambda root:(_ for _ in ()).throw(ValueError('fixture')))
    except hyd.TargetHold as e:assert str(e)=='TARGET_STATE_VALUEERROR'
    else:raise AssertionError('state failure accepted')
    assert engine.candidate_universe is old_universe and runtime.rc.discover is old_discovery
    print('[PASS] ORACLE504 target-pool, mismatch rejection, guarded hydration, saved-wallet routing, rollback of overrides')

if __name__=='__main__':tests()
