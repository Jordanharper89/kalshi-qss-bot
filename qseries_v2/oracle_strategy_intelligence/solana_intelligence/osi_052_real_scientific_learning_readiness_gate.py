from __future__ import annotations
import json
from pathlib import Path
def gate(root):
 required={
  "solana_reader":root/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_045_exact_solana_gmgn_postgresql_reader.py",
  "feature_extractor":root/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_047_real_solana_feature_extractor.py",
  "outcome_lineage":root/"runtime_state/solana_opportunities/oad314_forward_outcome_lineage.json",
  "outcome_endpoints":root/"runtime_state/solana_opportunities/oad314_physical_outcome_endpoints.json",
  "formula_engine":root/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_037_scientific_interaction_formula_discovery.py",
  "thesis_freeze":root/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_038_prospective_formula_thesis_freeze.py"}
 present={k:p.is_file() for k,p in required.items()}
 ep=root/"runtime_state/solana_opportunities/oad314_physical_outcome_endpoints.json"
 files=0
 if ep.is_file():
  try:files=int(json.loads(ep.read_text(encoding="utf-8")).get("physical_file_count",0))
  except Exception:pass
 return {"components_present":present,"outcome_physical_files":files,"real_learning_ready":all(present.values()) and files>0,"execution_authority":False,"read_only":True}
