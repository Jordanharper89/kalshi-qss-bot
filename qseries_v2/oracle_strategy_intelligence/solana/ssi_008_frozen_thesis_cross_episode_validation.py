from qseries_v2.oracle_strategy_intelligence.solana.ssi_006_certified_oad312_contract_bridge import FROZEN
def validate_episode_metadata(episodes):
 return tuple({"token":r.get("token") or r.get("token_address"),"history_rows":r.get("history_records") or r.get("history_rows") or r.get("history_count") or 0,"frozen_thesis":FROZEN} for r in episodes)
