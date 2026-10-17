"""ORACLE345 strict scanner-origin pair identity; immutable source, no guessing."""
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_344_scanner_align as a
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_343_unified_feed_recovery as old

def vetted(nom,pairs,heartbeat):
    if not heartbeat.get('ok'):raise ValueError('SCANNER_HEARTBEAT_STALE')
    if nom['producer']!=heartbeat['producer']:raise ValueError('SCANNER_PRODUCER_CHANGED')
    if old.nomination_age(nom,__import__('time').time_ns(),2500) is None:raise ValueError('NOMINATION_STALE')
    pair=a.matching_pair(nom,pairs)
    if not all(pair[k]==nom[k] for k in ('token','pump_pool','meteora_pool')):raise ValueError('IDENTITY_DRIFT')
    return pair
