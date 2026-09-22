from dataclasses import dataclass
from types import MappingProxyType
from .oad_012_subscription_partitioning import SubscriptionCoveragePlan, build_partition_subscribe_commands

OAD_016_BUILD_ID="OAD-016"
OAD_016_REVISION="OAD_016_KALSHI_RECONNECT_RESUBSCRIBE_RECOVERY_V1"

@dataclass(frozen=True)
class ReconnectRecoveryPlan:
    reconnect_required:bool
    relist_subscriptions_required:bool
    resubscribe_required:bool
    resnapshot_orderbooks_required:bool
    universe_reconcile_required:bool

def build_reconnect_recovery_plan(connection_lost,subscription_state_unknown=True):
    reconnect=bool(connection_lost)
    relist=bool(reconnect or subscription_state_unknown)
    resub=bool(reconnect or subscription_state_unknown)
    snapshot=bool(reconnect or subscription_state_unknown)
    reconcile=bool(reconnect)
    return ReconnectRecoveryPlan(reconnect,relist,resub,snapshot,reconcile)

def build_recovery_subscribe_commands(plan,coverage_plan):
    if not isinstance(plan,ReconnectRecoveryPlan):
        raise ValueError("certified recovery plan required")
    if not isinstance(coverage_plan,SubscriptionCoveragePlan):
        raise ValueError("certified coverage plan required")
    if not plan.resubscribe_required:
        return ()
    return build_partition_subscribe_commands(coverage_plan)

def recovery_ready(connected,subscriptions_restored,snapshots_restored,universe_reconciled):
    return bool(connected and subscriptions_restored and snapshots_restored and universe_reconciled)

def build_oad_016_certification_manifest():
    return MappingProxyType({"build_id":OAD_016_BUILD_ID,"revision":OAD_016_REVISION,
        "reconnect":True,"list_subscriptions_after_reconnect":True,"resubscribe":True,
        "orderbook_resnapshot":True,"universe_reconcile":True,"execution":False})

def verify_oad_016_kalshi_reconnect_resubscribe_recovery():
    from .oad_012_subscription_partitioning import partition_subscriptions
    p=build_reconnect_recovery_plan(True)
    c=partition_subscriptions(("A","B"),partition_size=1)
    cmds=build_recovery_subscribe_commands(p,c)
    return p.reconnect_required and p.resubscribe_required and len(cmds)==2 and recovery_ready(True,True,True,True)
