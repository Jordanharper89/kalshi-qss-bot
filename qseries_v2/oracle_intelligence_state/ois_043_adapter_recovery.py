from dataclasses import dataclass
@dataclass(frozen=True)
class AdapterRecoveryPlan:
 reconnect_required:bool; resubscribe_required:bool; reconcile_universe_required:bool; replay_gap_check_required:bool
def build_adapter_recovery_plan(connection_lost,subscription_lost,possible_gap):
 reconnect=bool(connection_lost); resub=bool(subscription_lost or reconnect); reconcile=resub; gap=bool(possible_gap or reconnect)
 return AdapterRecoveryPlan(reconnect,resub,reconcile,gap)
def recovery_complete(connected,subscribed,universe_reconciled,gap_checked): return bool(connected and subscribed and universe_reconciled and gap_checked)
def verify_ois_043_live_adapter_reconnect_resubscription_recovery():
 p=build_adapter_recovery_plan(True,False,False)
 return p.reconnect_required and p.resubscribe_required and p.reconcile_universe_required and p.replay_gap_check_required and recovery_complete(True,True,True,True)
