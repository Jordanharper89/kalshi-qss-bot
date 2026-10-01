from __future__ import annotations
import math,statistics

FEATURES=("buy_share_2s","buy_share_5s","pressure_accel","unique_buyers_5s",
          "momentum_5s","wallet_quality","birth_age_seconds","score")

def f(v,d=0.0):
    try:
        x=float(v)
        return x if math.isfinite(x) else float(d)
    except Exception:return float(d)

def model(trades,base_gate=.56,base_stop=.07,base_take=.12,base_hold=90.0):
    xs=list(trades)[-200:]
    wins=[x for x in xs if f(x.get("net_pnl_usdc"))>0]
    losses=[x for x in xs if f(x.get("net_pnl_usdc"))<=0]
    net=sum(f(x.get("net_pnl_usdc")) for x in xs)
    wr=len(wins)/len(xs) if xs else None
    out={"sample":len(xs),"wins":len(wins),"losses":len(losses),"net_pnl_usdc":net,"win_rate":wr,
         "admission_score":base_gate,"stop_loss":base_stop,"take_profit":base_take,
         "max_hold_seconds":base_hold,"promoted":[],"demoted":[],"features":{}}
    if len(xs)>=8 and len(wins)>=4 and len(losses)>=2:
        for feat in FEATURES:
            w=[f((x.get("signal") or {}).get(feat)) for x in wins]
            l=[f((x.get("signal") or {}).get(feat)) for x in losses]
            wm=sum(w)/len(w);lm=sum(l)/len(l);scale=max(abs(wm),abs(lm),1e-9)
            sep=(wm-lm)/scale
            higher_good=feat!="birth_age_seconds"
            judged=sep if higher_good else -sep
            out["features"][feat]={"win_mean":wm,"loss_mean":lm,"separation":judged}
            if judged>.12:out["promoted"].append(feat)
            elif judged<-.12:out["demoted"].append(feat)
        if net>0 and wr is not None and wr>=.60:out["admission_score"]=max(.46,base_gate-.04)
        elif net<=0 or (wr is not None and wr<.48):out["admission_score"]=min(.72,base_gate+.07)
    if len(xs)>=12 and wins and losses:
        mfe=[f(x.get("mfe")) for x in wins if x.get("mfe") is not None]
        mae=[abs(f(x.get("mae"))) for x in losses if x.get("mae") is not None]
        holds=[f(x.get("closed_unix"))-f(x.get("opened_unix")) for x in wins if x.get("closed_unix")]
        if mfe:out["take_profit"]=max(.06,min(.25,statistics.median(mfe)*.72))
        if mae:out["stop_loss"]=max(.035,min(.12,statistics.median(mae)*.80))
        if holds:out["max_hold_seconds"]=max(8,min(90,statistics.median(holds)*1.6))
    return out

def adjusted_score(sig,m):
    s=f(sig.get("score"))
    for feat in m.get("promoted") or []:
        st=(m.get("features") or {}).get(feat) or {};v=f(sig.get(feat))
        if feat=="birth_age_seconds":
            if v<=f(st.get("win_mean")):s+=.02
            elif v>=f(st.get("loss_mean")):s-=.02
        else:
            if v>=f(st.get("win_mean")):s+=.02
            elif v<=f(st.get("loss_mean")):s-=.02
    return max(0.0,min(1.0,s))
