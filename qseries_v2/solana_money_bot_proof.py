from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.solana_money_bot import UnifiedSolanaMoneyBot, ingest, REVISION

PROOF_REVISION="QSB-002B-TRUTH-CERTIFIED-001C-COMPATIBLE"

SOURCE_ROOTS=(
    Path("runtime_state/solana_opportunities"),
    Path("runtime/solana"),
    Path("runtime/strategy_discovery"),
)

def jread(p,default):
    try:return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:return default

def count_source_files(root):
    n=0
    sample=[]
    for rel in SOURCE_ROOTS:
        base=root/rel
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in (".json",".jsonl"):
                n+=1
                if len(sample)<15:
                    try: sample.append(str(p.relative_to(root)))
                    except Exception: sample.append(str(p))
    return n,sample

def real_repo_proof(root):
    root=Path(root).resolve()
    file_count,sample=count_source_files(root)

    # Use the exact ingest() that exists in QSB-001C.
    rows=ingest(root)

    bot=UnifiedSolanaMoneyBot(root)
    histories=bot.histories(rows)
    minpts=bot.cfg.min_history_points
    multipoint={k:v for k,v in histories.items() if len(v)>=minpts}

    candidates=[]
    for pool,h in multipoint.items():
        s=bot.detect_second_leg(h)
        if s:candidates.append(s)

    newest=max((float(r["t"]) for r in rows),default=0.0)
    age=(time.time()-newest) if newest else None
    identities=sum(bool(r.get("token_mint")) for r in rows)

    trades=jread(root/"runtime_state/qseries/solana_money_bot/trades.json",{"trades":[]}).get("trades",[])
    closed=[t for t in trades if t.get("status")=="CLOSED" and t.get("mode")=="PAPER"]
    pnl=[float(t.get("realized_pnl_usdc") or 0) for t in closed]

    proof={
      "revision":PROOF_REVISION,
      "bot_revision":REVISION,
      "real_files_found":file_count,
      "real_source_rows":len(rows),
      "real_markets":len(histories),
      "real_markets_with_required_history":len(multipoint),
      "real_rows_with_token_identity":identities,
      "newest_observation_age_seconds":age,
      "real_strategy_candidates_now":len(candidates),
      "sample_source_files":sample,
      "closed_paper_trades":len(closed),
      "paper_total_realized_pnl_usdc":sum(pnl),
      "paper_mean_realized_pnl_usdc":(sum(pnl)/len(pnl)) if pnl else None,
      "paper_positive_frequency":(sum(x>0 for x in pnl)/len(pnl)) if pnl else None,
      "mechanical_build_proven":True,
      "live_repo_ingestion_proven":len(rows)>0,
      "real_market_path_proven":len(multipoint)>0,
      "token_identity_proven":identities>0,
      "profitability_proven":False,
    }

    if len(pnl)>=20 and sum(pnl)>0 and (sum(x>0 for x in pnl)/len(pnl))>0.5:
        proof["profitability_proven"]=True

    proof["physical_integration_pass"]=all([
        proof["live_repo_ingestion_proven"],
        proof["real_market_path_proven"],
        proof["token_identity_proven"],
    ])

    out=root/"runtime_state/qseries/solana_money_bot/proof.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(proof,indent=2,sort_keys=True),encoding="utf-8")
    return proof

def print_proof(p):
    print("="*118)
    print(" QSB-002B TRUTH CERTIFICATION")
    print("="*118)
    print("[BOT REVISION]",p["bot_revision"])
    print("[REAL FILES]",p["real_files_found"])
    print("[REAL SOURCE ROWS]",p["real_source_rows"])
    print("[REAL MARKETS]",p["real_markets"])
    print("[MARKETS WITH REQUIRED HISTORY]",p["real_markets_with_required_history"])
    print("[ROWS WITH TOKEN IDENTITY]",p["real_rows_with_token_identity"])
    print("[NEWEST AGE SEC]",p["newest_observation_age_seconds"])
    print("[REAL STRATEGY CANDIDATES NOW]",p["real_strategy_candidates_now"])
    print("[CLOSED PAPER TRADES]",p["closed_paper_trades"])
    print("[PAPER REALIZED PNL USDC]",p["paper_total_realized_pnl_usdc"])
    print("[LIVE REPO INGESTION PROVEN]",p["live_repo_ingestion_proven"])
    print("[REAL MARKET PATH PROVEN]",p["real_market_path_proven"])
    print("[TOKEN IDENTITY PROVEN]",p["token_identity_proven"])
    print("[PROFITABILITY PROVEN]",p["profitability_proven"])
    print("[PHYSICAL INTEGRATION PASS]",p["physical_integration_pass"])
    print("[PROOF FILE] runtime_state/qseries/solana_money_bot/proof.json")
    print("="*118)

def main():
    p=real_repo_proof(Path.cwd())
    print_proof(p)
    raise SystemExit(0 if p["physical_integration_pass"] else 2)

if __name__=="__main__":
    main()
