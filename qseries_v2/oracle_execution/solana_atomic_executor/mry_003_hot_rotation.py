from __future__ import annotations
HOT_TARGET=20
ACCOUNT_BUDGET=480

def _rank(row):
    src=0 if row.get("source")=="MRIYA_HOT" else 1
    age=row.get("source_age")
    try:age=float(age)
    except Exception:age=1e18
    return (src,age,int(row.get("account_cost") or 999999),str(row.get("token")))

def select_hot(inventory,target=HOT_TARGET,account_budget=ACCOUNT_BUDGET,cursor=0):
    rows=sorted(list(inventory or []),key=_rank)
    if not rows:return []
    n=len(rows);cursor=int(cursor)%n
    rows=rows[cursor:]+rows[:cursor]
    selected=[];used=0
    for row in rows:
        cost=max(1,int(row.get("account_cost") or 1))
        if selected and used+cost>int(account_budget):continue
        selected.append(row);used+=cost
        if len(selected)>=int(target):break
    return selected

def hot_view(state,selected):
    chosen={int(x["index"]) for x in selected}
    preg={}
    addresses=[]
    old_preg=state.get("preg",{})
    for addr,item in old_preg.items():
        try:idx=int(item[0])
        except Exception:continue
        if idx in chosen:
            preg[addr]=item
            if addr not in addresses:addresses.append(addr)
    view=dict(state)
    view["preg"]=preg
    view["addresses"]=addresses
    view["_mry_hot_tokens"]=[str(x["token"]) for x in selected]
    return view
