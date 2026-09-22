from __future__ import annotations
from dataclasses import dataclass

OAD_052_BUILD_ID="OAD-052"
OAD_052_REVISION="OAD_052_DYNAMIC_ORDERBOOK_PARTITION_ROTATION_V1"

@dataclass(frozen=True)
class SubscriptionRotation:
    add_markets:tuple[str,...]
    delete_markets:tuple[str,...]
    unchanged_markets:tuple[str,...]

def compute_subscription_rotation(current_markets,target_markets):
    current=set(str(x) for x in current_markets if str(x))
    target=set(str(x) for x in target_markets if str(x))
    return SubscriptionRotation(
        tuple(sorted(target-current)),
        tuple(sorted(current-target)),
        tuple(sorted(current & target)),
    )

def build_update_subscription_command(command_id,sids,market_tickers,action):
    action=str(action)
    if action not in ("add_markets","delete_markets"):
        raise ValueError("action must be add_markets or delete_markets")
    sids=tuple(int(x) for x in sids)
    markets=tuple(str(x) for x in market_tickers if str(x))
    if not sids or not markets:
        raise ValueError("sids and market_tickers required")
    return {
        "id":int(command_id),
        "cmd":"update_subscription",
        "params":{
            "sids":list(sids),
            "market_tickers":list(markets),
            "action":action,
        },
    }

def build_rotation_commands(rotation,sids,start_command_id=1000):
    commands=[]
    cid=int(start_command_id)
    if rotation.add_markets:
        commands.append(build_update_subscription_command(cid,sids,rotation.add_markets,"add_markets"))
        cid+=1
    if rotation.delete_markets:
        commands.append(build_update_subscription_command(cid,sids,rotation.delete_markets,"delete_markets"))
    return tuple(commands)

def verify_oad_052_dynamic_orderbook_partition_rotation():
    r=compute_subscription_rotation(("A","B"),("B","C"))
    cmds=build_rotation_commands(r,(7,))
    return r.add_markets==("C",) and r.delete_markets==("A",) and len(cmds)==2 and cmds[0]["cmd"]=="update_subscription"
