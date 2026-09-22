from dataclasses import dataclass
OAD_042_BUILD_ID="OAD-042"
OAD_042_REVISION="OAD_042_PARTITIONED_PERSISTENT_CANONICAL_PERSISTENCE_V1"

@dataclass(frozen=True)
class PartitionPersistenceState:
    partition_id:int
    connected:bool
    subscription_ready:bool
    events_seen:int
    persisted:int
    reconnects:int
    healthy:bool

def build_partition_persistence_state(partition_id,connected,subscription_ready,events_seen,persisted,reconnects):
    pid=int(partition_id); events=int(events_seen); saved=int(persisted); rec=int(reconnects)
    if pid<1 or min(events,saved,rec)<0:
        raise ValueError("valid partition counters required")
    healthy=bool(connected and subscription_ready and saved<=events)
    return PartitionPersistenceState(pid,bool(connected),bool(subscription_ready),events,saved,rec,healthy)

def summarize_partition_persistence(states):
    states=tuple(states)
    if not states:
        raise ValueError("partition states required")
    ids=tuple(x.partition_id for x in states)
    if len(set(ids))!=len(ids):
        raise ValueError("duplicate partition id")
    return {
        "partitions":len(states),
        "healthy_partitions":sum(1 for x in states if x.healthy),
        "events_seen":sum(x.events_seen for x in states),
        "persisted":sum(x.persisted for x in states),
        "reconnects":sum(x.reconnects for x in states),
        "complete":all(x.healthy for x in states),
    }

def verify_oad_042_partitioned_persistent_canonical_persistence():
    a=build_partition_persistence_state(1,True,True,5,5,0)
    b=build_partition_persistence_state(2,True,True,3,3,1)
    x=summarize_partition_persistence((a,b))
    return x["complete"] and x["persisted"]==8 and x["partitions"]==2
