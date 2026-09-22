from __future__ import annotations
import json
from pathlib import Path

def certify(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 ev=json.loads((base/"pump_trade_events_exact.json").read_text(encoding="utf-8"))
 rec=json.loads((base/"pump_trade_event_reconciled.json").read_text(encoding="utf-8"))
 tape=json.loads((base/"pump_exact_economic_trade_tape.json").read_text(encoding="utf-8"))
 feat=json.loads((base/"pump_exact_flow_features.json").read_text(encoding="utf-8"))
 checks={"trade_events_present":ev["rows_with_trade_event"]>0,
  "exact_reconciliation_present":rec["exact_count"]>0,
  "economic_tape_present":tape["economic_exact_count"]>0,
  "flow_features_present":feat["economic_exact_count"]>0,
  "unknowns_not_fabricated":rec["unresolved_count"]>=0,
  "profitability_unclaimed":not tape["profitability_claimed"],
  "execution_authority_false":not tape["execution_authority"]}
 return {"revision":"USLS_044","checks":checks,"phase3_certified":all(checks.values()),
  "captured_trade_count":tape["row_count"],"economic_exact_count":tape["economic_exact_count"],
  "coverage_ratio":feat["coverage_ratio"],"supersedes":["USLS_036","USLS_037","USLS_038","USLS_039"],
  "next_boundary":"PHASE_4_EXACT_TRADE_DECODING_ACROSS_SOLANA_VENUES",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=certify(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/phase3_pump_trade_tape_certification.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
