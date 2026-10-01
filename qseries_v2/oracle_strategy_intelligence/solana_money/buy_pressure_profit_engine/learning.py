from __future__ import annotations
import math

FEATURES=("buy_share_2s","buy_share_5s","pressure_accel","unique_buyers_5s",
          "momentum_5s","largest_buyer_share","birth_age_seconds","quality_score")

def f(v,d=0.0):
    try:
        x=float(v);return x if math.isfinite(x) else float(d)
    except Exception:return float(d)

def learn(trades,base_quality=.72):
    xs=[x for x in trades if x.get("evidence_valid",True)]
    xs=xs[-200:]
    wins=[x for x in xs if f(x.get("net_pnl_usdc"))>0]
    losses=[x for x in xs if f(x.get("net_pnl_usdc"))<=0]
    net=sum(f(x.get("net_pnl_usdc")) for x in xs)
    wr=len(wins)/len(xs) if xs else None
    out={"sample":len(xs),"wins":len(wins),"losses":len(losses),"net_pnl_usdc":net,
         "win_rate":wr,"quality_floor":base_quality,"promoted":[],"demoted":[],"features":{},
         "hard_max_hold_seconds":90.0}
    if len(xs)>=8 and len(wins)>=3 and len(losses)>=3:
        for feat in FEATURES:
            w=[f((x.get("signal") or {}).get(feat)) for x in wins]
            l=[f((x.get("signal") or {}).get(feat)) for x in losses]
            wm=sum(w)/len(w);lm=sum(l)/len(l);scale=max(abs(wm),abs(lm),1e-9)
            higher=feat not in ("largest_buyer_share","birth_age_seconds")
            sep=(wm-lm)/scale
            judged=sep if higher else -sep
            out["features"][feat]={"win_mean":wm,"loss_mean":lm,"separation":judged}
            if judged>.15:out["promoted"].append(feat)
            elif judged<-.15:out["demoted"].append(feat)
        # Learning may tighten a losing strategy immediately. It is NOT
        # allowed to loosen the entry floor until fresh evidence is adequate.
        if net<=0 or (wr is not None and wr<.50):
            out["quality_floor"]=min(.90,base_quality+.06)
        elif len(xs)>=25 and net>0 and wr is not None and wr>=.55:
            out["quality_floor"]=max(.68,base_quality-.02)
    return out
