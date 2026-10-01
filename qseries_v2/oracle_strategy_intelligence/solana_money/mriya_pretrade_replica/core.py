from __future__ import annotations
import json,math,time
from pathlib import Path

WSOL="So11111111111111111111111111111111111111112"
CLEAN_MAX_GROSS_BPS=500.0
MIN_FAMILY_WINS=2
MIN_EXPECTED_NET_BPS=10.0

def _f(x,default=None):
    try:
        v=float(x)
        return v if math.isfinite(v) else default
    except Exception:return default

def load_report(root):
    p=Path(root)/"runtime_state/qseries/qsb035_mriya_strategy_fingerprint/report.json"
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return {"records":[],"summary":{}}

def clean_closed_records(report):
    out=[]
    for r in report.get("records") or []:
        if r.get("failed"):continue
        c=r.get("chain") or {}
        bps=_f(c.get("gross_bps"))
        if not c.get("contiguous") or not c.get("closed") or bps is None:continue
        if bps<=0 or bps>CLEAN_MAX_GROSS_BPS:continue
        legs=c.get("legs") or []
        if len(legs)<2:continue
        out.append(r)
    return out

def family_key(r):
    return tuple(r.get("venue_chain") or ())

def learned_templates(report):
    rows=clean_closed_records(report);groups={}
    for r in rows:groups.setdefault(family_key(r),[]).append(r)
    out=[]
    for fam,rs in groups.items():
        if len(rs)<MIN_FAMILY_WINS:continue
        first=(rs[0].get("chain") or {}).get("legs") or []
        # Exact replica template only when the same mint path repeats.
        paths=[]
        for r in rs:
            legs=(r.get("chain") or {}).get("legs") or []
            if not legs:continue
            path=[legs[0].get("input_asset")]+[x.get("output_asset") for x in legs]
            paths.append(tuple(path))
        counts={}
        for p in paths:counts[p]=counts.get(p,0)+1
        path,maxn=max(counts.items(),key=lambda kv:kv[1])
        if maxn<MIN_FAMILY_WINS:continue
        sizes=[_f((r.get("chain") or {}).get("start_amount")) for r in rs]
        sizes=[x for x in sizes if x and x>0]
        bps=[_f((r.get("chain") or {}).get("gross_bps")) for r in rs]
        bps=[x for x in bps if x is not None]
        out.append({"venues":fam,"mint_path":path,"wins":len(rs),"repeat_path_wins":maxn,
                    "observed_size_min":min(sizes) if sizes else None,
                    "observed_size_max":max(sizes) if sizes else None,
                    "observed_avg_gross_bps":sum(bps)/len(bps) if bps else None})
    return out

def evaluate_roundtrip(start_amount,quotes,tx_cost_anchor=0.0,min_net_bps=MIN_EXPECTED_NET_BPS):
    amount=float(start_amount);legs=[]
    for q in quotes:
        if not q.get("exact"):return {"qualified":False,"reason":"NON_EXACT_QUOTE","legs":legs}
        if q.get("input_asset")!=q.get("expected_input_asset"):
            return {"qualified":False,"reason":"ASSET_PATH_MISMATCH","legs":legs}
        qin=float(q["input_amount"])
        if abs(qin-amount)>max(1e-12,abs(amount)*1e-9):
            return {"qualified":False,"reason":"AMOUNT_CHAIN_MISMATCH","legs":legs}
        amount=float(q["output_amount"]);legs.append(q)
    net=amount-float(start_amount)-float(tx_cost_anchor)
    bps=net/float(start_amount)*10000.0
    return {"qualified":bps>=float(min_net_bps),"reason":"PASS" if bps>=float(min_net_bps) else "NET_EDGE_TOO_SMALL",
            "start_amount":float(start_amount),"end_amount":amount,"tx_cost_anchor":float(tx_cost_anchor),
            "net_amount":net,"net_bps":bps,"legs":legs}

def reject_decimal_anomaly(record):
    c=record.get("chain") or {};bps=_f(c.get("gross_bps"))
    return bps is None or bps<=0 or bps>CLEAN_MAX_GROSS_BPS
