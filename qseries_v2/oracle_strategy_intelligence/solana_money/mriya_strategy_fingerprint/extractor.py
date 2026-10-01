from __future__ import annotations
import math,time
from collections import Counter,defaultdict
from pathlib import Path
from urllib.error import HTTPError
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_route_anatomy.anatomy import analyze_target
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_route_anatomy.persistence import read_json,write_json
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_captured_route_replay.replay import captured_targets

WSOL="So11111111111111111111111111111111111111112"

def f(v,d=0.0):
    try:
        x=float(v);return x if math.isfinite(x) else float(d)
    except Exception:return float(d)

def route_chain(a):
    legs=[x for x in a.get("legs") or [] if x.get("resolved")]
    if not legs:return {"contiguous":False,"closed":False,"reason":"NO_RESOLVED_LEGS"}
    chain=[legs[0]]
    for leg in legs[1:]:
        if chain[-1].get("output_asset")!=leg.get("input_asset"):
            return {"contiguous":False,"closed":False,"reason":"RESOLVED_LEGS_NOT_CONTIGUOUS","legs":legs}
        chain.append(leg)
    first=chain[0];last=chain[-1]
    closed=first.get("input_asset")==last.get("output_asset")
    gross_return=(f(last.get("output_amount"))/f(first.get("input_amount"))-1) if closed and f(first.get("input_amount"))>0 else None
    return {"contiguous":True,"closed":closed,"legs":chain,
            "start_asset":first.get("input_asset"),"end_asset":last.get("output_asset"),
            "start_amount":f(first.get("input_amount")),"end_amount":f(last.get("output_amount")),
            "gross_return":gross_return,"gross_bps":gross_return*10000 if gross_return is not None else None}

def strategy_record(a):
    chain=route_chain(a)
    venues=tuple(x.get("venue") for x in chain.get("legs") or [])
    fee_sol=f(a.get("fee_lamports"))/1e9
    sol_native=f(a.get("wallet_sol_delta"))
    wsol_delta=f((a.get("wallet_token_deltas") or {}).get(WSOL))
    net_sol_equiv=None
    if a.get("closed_anchor_cycle") and not a.get("wallet_nonanchor_deltas"):
        anchors=a.get("wallet_anchor_deltas") or {}
        if set(anchors).issubset({"WSOL","SOL_NATIVE"}) and ("WSOL" in anchors or "SOL_NATIVE" in anchors):
            net_sol_equiv=f(anchors.get("WSOL"))+f(anchors.get("SOL_NATIVE"))
    return {
      "signature":a.get("signature"),"slot":a.get("slot"),"failed":bool(a.get("failed")),
      "venues_all":tuple(a.get("venues") or []),"venue_chain":venues,
      "chain":chain,"fee_lamports":a.get("fee_lamports"),"fee_sol":fee_sol,
      "compute_units":a.get("compute_units"),"wallet_sol_delta":sol_native,"wsol_delta":wsol_delta,
      "net_sol_equiv":net_sol_equiv,"closed_anchor_cycle":bool(a.get("closed_anchor_cycle")),
      "resolved_legs":a.get("resolved_legs"),"leg_count":a.get("leg_count"),
      "error":a.get("error"),"execution_authority":False,
    }

def summarize(records):
    wins=[x for x in records if not x["failed"]]
    fails=[x for x in records if x["failed"]]
    families=defaultdict(lambda:{"wins":0,"fails":0,"samples":0,"returns_bps":[],"net_sol":[],"fees_sol":[],"compute":[]})
    for r in records:
        key=" -> ".join(r["venue_chain"] or r["venues_all"]) or "UNKNOWN"
        d=families[key];d["samples"]+=1;d["fails" if r["failed"] else "wins"]+=1
        c=r.get("chain") or {}
        if c.get("gross_bps") is not None:d["returns_bps"].append(c["gross_bps"])
        if r.get("net_sol_equiv") is not None:d["net_sol"].append(r["net_sol_equiv"])
        d["fees_sol"].append(f(r.get("fee_sol")))
        if r.get("compute_units") is not None:d["compute"].append(int(r["compute_units"]))
    fam=[]
    for k,d in families.items():
        fam.append({
          "route":k,"samples":d["samples"],"wins":d["wins"],"fails":d["fails"],
          "win_rate":d["wins"]/d["samples"] if d["samples"] else None,
          "avg_gross_bps":sum(d["returns_bps"])/len(d["returns_bps"]) if d["returns_bps"] else None,
          "avg_net_sol_equiv":sum(d["net_sol"])/len(d["net_sol"]) if d["net_sol"] else None,
          "avg_fee_sol":sum(d["fees_sol"])/len(d["fees_sol"]) if d["fees_sol"] else None,
          "avg_compute_units":sum(d["compute"])/len(d["compute"]) if d["compute"] else None,
        })
    fam.sort(key=lambda x:(x["wins"],x["samples"]),reverse=True)
    return {
      "samples":len(records),"wins":len(wins),"fails":len(fails),
      "win_rate":len(wins)/len(records) if records else None,
      "closed_anchor_wins":sum((not x["failed"]) and x["closed_anchor_cycle"] for x in records),
      "route_families":fam,
      "successful_signatures":[x["signature"] for x in wins],
      "failed_signatures":[x["signature"] for x in fails],
      "execution_authority":False,
    }

class Fetcher:
    def __init__(self,rpc=None,spacing=2.6,max_retries=4):
        from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
        self.rpc=rpc or _rpc;self.spacing=float(spacing);self.max_retries=int(max_retries);self.last=0
        self.rate_limits=0;self.errors=0
    def _pace(self):
        d=self.spacing-(time.monotonic()-self.last)
        if d>0:time.sleep(d)
    def fetch(self,slot):
        for attempt in range(self.max_retries):
            self._pace()
            try:
                b=self.rpc("getBlock",[int(slot),{"encoding":"jsonParsed","transactionDetails":"full",
                  "rewards":False,"commitment":"confirmed","maxSupportedTransactionVersion":1}],12.0)
                self.last=time.monotonic()
                if isinstance(b,dict):return b,attempt+1
                self.errors+=1
            except HTTPError as e:
                self.last=time.monotonic()
                if getattr(e,"code",None)==429:
                    self.rate_limits+=1
                    time.sleep(min(8.0,2.0*(attempt+1)))
                    continue
                self.errors+=1;break
            except Exception:
                self.last=time.monotonic();self.errors+=1;break
        return None,self.max_retries

def run(root:Path,fetcher=None):
    root=Path(root).resolve();fetcher=fetcher or Fetcher()
    q34=root/"runtime_state/qseries/qsb034_mriya_captured_route_replay/report.json"
    prior=read_json(q34,{"routes":[]})
    bysig={str(x.get("signature") or ""):x for x in prior.get("routes") or [] if x.get("signature")}
    seeds=captured_targets(root)
    byslot=defaultdict(set)
    for x in seeds:
        byslot[int(x["slot"])].add(str(x.get("signature") or ""))
    recovered_slots=[];missed=[]
    for slot,wanted in sorted(byslot.items()):
        already=[s for s in wanted if s and s in bysig]
        if wanted and len(already)==len([s for s in wanted if s]):
            continue
        b,attempts=fetcher.fetch(slot)
        if not isinstance(b,dict):
            missed.append(slot);print("[RETRY_MISS] slot=%d attempts=%d"%(slot,attempts),flush=True);continue
        bt=b.get("blockTime");found=0
        for tx in b.get("transactions") or []:
            a=analyze_target(tx,slot,bt)
            if not a or not a.get("executor_present") or not a.get("signature"):continue
            if wanted and all(wanted) and a["signature"] not in wanted:continue
            bysig[a["signature"]]=a;found+=1
        recovered_slots.append({"slot":slot,"found":found,"attempts":attempts})
        print("[RECOVERED_SLOT] slot=%d target_routes=%d attempts=%d"%(slot,found,attempts),flush=True)

    anatomies=list(bysig.values())
    anatomies.sort(key=lambda x:(int(x.get("slot") or 0),str(x.get("signature") or "")))
    records=[strategy_record(a) for a in anatomies]
    summary=summarize(records)
    report={"summary":summary,"records":records,"anatomies":anatomies,
            "recovered_slots":recovered_slots,"missed_slots":missed,
            "rpc429":fetcher.rate_limits,"errors":fetcher.errors,"execution_authority":False}
    out=root/"runtime_state/qseries/qsb035_mriya_strategy_fingerprint/report.json"
    write_json(out,report)

    for r in records:
        if r["failed"]:
            print("[FAIL_PATTERN] sig=%s venues=%s fee_sol=%.9f cu=%s error=%s"%(
              r["signature"],r["venues_all"],r["fee_sol"],r["compute_units"],r["error"]),flush=True)
            continue
        c=r["chain"]
        print("[WIN_PATTERN] sig=%s chain=%s closed=%s gross_bps=%s net_sol_equiv=%s fee_sol=%.9f cu=%s"%(
          r["signature"],r["venue_chain"],c.get("closed"),
          ("%.2f"%c["gross_bps"]) if c.get("gross_bps") is not None else "NA",
          ("%.9f"%r["net_sol_equiv"]) if r["net_sol_equiv"] is not None else "NA",
          r["fee_sol"],r["compute_units"]),flush=True)
        for i,leg in enumerate(c.get("legs") or [],1):
            print("[ROUTE_LEG %d] %s %g %s -> %g %s"%(
              i,leg["venue"],leg["input_amount"],leg["input_asset"],leg["output_amount"],leg["output_asset"]),flush=True)

    print("[STRATEGY_SUMMARY] samples=%d wins=%d fails=%d win_rate=%s closed_anchor_wins=%d"%(
      summary["samples"],summary["wins"],summary["fails"],
      ("%.4f"%summary["win_rate"]) if summary["win_rate"] is not None else "NA",
      summary["closed_anchor_wins"]),flush=True)
    for x in summary["route_families"]:
        print("[FAMILY] route=%s samples=%d wins=%d fails=%d win_rate=%.4f avg_gross_bps=%s avg_net_sol=%s avg_fee_sol=%s avg_cu=%s"%(
          x["route"],x["samples"],x["wins"],x["fails"],x["win_rate"],
          ("%.2f"%x["avg_gross_bps"]) if x["avg_gross_bps"] is not None else "NA",
          ("%.9f"%x["avg_net_sol_equiv"]) if x["avg_net_sol_equiv"] is not None else "NA",
          ("%.9f"%x["avg_fee_sol"]) if x["avg_fee_sol"] is not None else "NA",
          ("%.0f"%x["avg_compute_units"]) if x["avg_compute_units"] is not None else "NA"),flush=True)
    print("[RECOVERY] recovered=%d missed=%d rpc429=%d errors=%d"%(
      len(recovered_slots),len(missed),fetcher.rate_limits,fetcher.errors),flush=True)
    return report
