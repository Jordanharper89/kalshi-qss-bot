from __future__ import annotations
import time
from pathlib import Path
from urllib.error import HTTPError
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_route_anatomy.anatomy import analyze_target
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_route_anatomy.persistence import read_json,write_json

KNOWN_SLOTS=(
450205534,450205602,450205989,450206036,450206183,450206206,
450206333,450206609,450206610,450206656,450206679,
)

def captured_targets(root:Path):
    root=Path(root).resolve()
    paths=(
      root/"runtime_state/qseries/qsb032_public_rpc_slot_batched_mriya_arb/ledger.json",
      root/"runtime_state/qseries/qsb033_mriya_exact_route_anatomy/routes.json",
    )
    rows=[];seen=set()
    for p in paths:
        d=read_json(p,{})
        for key in ("target_transactions","routes"):
            for x in d.get(key) or []:
                try:s=int(x.get("slot") or 0)
                except Exception:s=0
                sig=str(x.get("signature") or "")
                if s<=0:continue
                k=(s,sig)
                if k in seen:continue
                seen.add(k);rows.append({"slot":s,"signature":sig})
    for s in KNOWN_SLOTS:
        if not any(x["slot"]==s for x in rows):
            rows.append({"slot":s,"signature":""})
    rows.sort(key=lambda x:(x["slot"],x["signature"]))
    return rows

class BlockFetcher:
    def __init__(self,rpc=None,spacing=.45):
        from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
        self.rpc=rpc or _rpc;self.spacing=float(spacing);self.last=0.0
        self.rate_limits=0;self.errors=0;self.blocks=0
    def fetch(self,slot):
        d=self.spacing-(time.monotonic()-self.last)
        if d>0:time.sleep(d)
        try:
            b=self.rpc("getBlock",[int(slot),{"encoding":"jsonParsed","transactionDetails":"full",
                "rewards":False,"commitment":"confirmed","maxSupportedTransactionVersion":1}],10.0)
            self.last=time.monotonic()
            if isinstance(b,dict):self.blocks+=1
            return b,False
        except HTTPError as e:
            self.last=time.monotonic()
            if getattr(e,"code",None)==429:
                self.rate_limits+=1;return None,True
            self.errors+=1;return None,False
        except Exception:
            self.last=time.monotonic();self.errors+=1;return None,False

def replay(root:Path,fetcher=None):
    root=Path(root).resolve();fetcher=fetcher or BlockFetcher()
    seeds=captured_targets(root)
    out={"seed_count":len(seeds),"routes":[],"slots":[],"rpc429":0,"errors":0}
    byslot={}
    for x in seeds:
        byslot.setdefault(x["slot"],set())
        if x["signature"]:byslot[x["slot"]].add(x["signature"])
    for slot,wanted in sorted(byslot.items()):
        block,limited=fetcher.fetch(slot)
        if limited:
            out["rpc429"]+=1
            print("[RPC429] slot=%d retry_later=True"%slot,flush=True)
            continue
        if not isinstance(block,dict):
            print("[MISS] slot=%d"%slot,flush=True);continue
        bt=block.get("blockTime");found=0
        for tx in block.get("transactions") or []:
            a=analyze_target(tx,slot,bt)
            if not a or not a.get("executor_present"):continue
            if wanted and a["signature"] not in wanted:continue
            out["routes"].append(a);found+=1
            if a["failed"]:
                print("[FAIL] sig=%s slot=%d venues=%s fee=%s cu=%s error=%s"%(
                    a["signature"],slot,a["venues"],a["fee_lamports"],a["compute_units"],a["error"]),flush=True)
            else:
                print("[WIN] sig=%s slot=%d venues=%s closed=%s anchor=%s nonanchor=%s legs=%d resolved=%d"%(
                    a["signature"],slot,a["venues"],a["closed_anchor_cycle"],a["wallet_anchor_deltas"],
                    a["wallet_nonanchor_deltas"],a["leg_count"],a["resolved_legs"]),flush=True)
                for i,leg in enumerate(a["legs"],1):
                    if leg.get("resolved"):
                        print("[LEG %d] %s %g %s -> %g %s rate=%g"%(
                            i,leg["venue"],leg["input_amount"],leg["input_asset"],
                            leg["output_amount"],leg["output_asset"],leg["effective_output_per_input"]),flush=True)
                    else:
                        print("[LEG %d] %s UNRESOLVED transfers=%d reason=%s"%(
                            i,leg["venue"],len(leg["transfers"]),leg["resolution_reason"]),flush=True)
        out["slots"].append({"slot":slot,"wanted_signatures":sorted(wanted),"found":found})
        print("[SLOT] slot=%d wanted=%d found=%d"%(slot,len(wanted),found),flush=True)
    out["rpc429"]=fetcher.rate_limits;out["errors"]=fetcher.errors
    p=root/"runtime_state/qseries/qsb034_mriya_captured_route_replay/report.json"
    write_json(p,out)
    return out
