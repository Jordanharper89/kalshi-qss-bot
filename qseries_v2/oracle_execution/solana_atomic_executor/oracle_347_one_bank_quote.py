"""ORACLE347 strict context-slot bank quote for nominated original direction/size."""
import time,collections
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_343_unified_feed_recovery as old
from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_bank_requote as bridge
from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as decoder
from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18

def reprice(nom,cat,roles,rpc_url,decimals=None):
    if not cat.get('discovery_complete') or cat['bin_selected']!=cat['bin_total']:raise ValueError('ARRAY_CATALOG_INCOMPLETE')
    # A candidate's source slot acts as lower bound, NOT a same-slot assertion.
    keys=sorted(k for k,rr in roles.items() if any(t==nom['token'] for t,_ in rr))
    if not 6<=len(keys)<=100:raise ValueError('BANK_ACCOUNT_COUNT_OUT_OF_BOUNDS')
    if not {'PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT','DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE'}.issubset({role for k in keys for t,role in roles[k] if t==nom['token']}):raise ValueError('BANK_REQUIRED_ROLES_MISSING')
    start=time.time_ns()
    response=witness.rpc(rpc_url,'getMultipleAccounts',[keys,{'encoding':'base64','commitment':'processed','minContextSlot':int(nom['slot'])}],collections.Counter(),retries=1)
    rows,slot=bridge.bank_rows(response,keys,int(nom['slot']),start)
    if slot<int(nom['slot']):raise ValueError('BANK_CONTEXT_BEHIND_SCANNER')
    if decimals is None:decimals=bridge.mint_metadata(rpc_url,[nom['token']])
    snap,lin=bridge.prepare_snapshot(cat,rows,roles,decimals,start-1,core,decoder)
    if lin['slot_min']!=slot or lin['slot_max']!=slot:raise ValueError('BANK_MIXED_CONTEXT')
    quote=bridge.directional_ladder(snap,q18,core,requested=(nom['direction'],nom['size_lamports']/1e9))
    exact=quote.get('requested_exact')
    if exact is None:raise ValueError('BANK_ORIGINAL_DIRECTION_UNPRICED')
    end=time.time_ns();elapsed=(end-start)/1e6
    return dict(token=nom['token'],direction=nom['direction'],size_lamports=nom['size_lamports'],scanner_slot=nom['slot'],bank_slot=slot,scanner_gross=nom['gross_lamports'],bank_gross=int(exact['gross_lamports']),account_count=len(keys),single_context_verified=True,bank_elapsed_ms=round(elapsed,2),quote_ms=quote['quote_ms'],gate='BANK_GROSS_POSITIVE' if int(exact['gross_lamports'])>0 and elapsed<=2000 else 'HOLD_NONPOSITIVE_OR_EXPIRED',signing=False,broadcast=False)
