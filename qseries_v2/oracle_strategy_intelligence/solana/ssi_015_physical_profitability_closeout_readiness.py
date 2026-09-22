from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import audit,FROZEN_THESIS
from qseries_v2.oracle_strategy_intelligence.solana.ssi_013_exact_maturity_contract import certify as maturity_contract
from qseries_v2.oracle_strategy_intelligence.solana.ssi_014_physical_independence_leakage_boundary import certify as independence

def certify(root=None):
    a=audit(root);m=maturity_contract();i=independence(root)
    ready=(i["independent_tokens"]>=5 and i["duplicates"]==0 and
           all(x["experiences"]>0 for x in a["episodes"]) and
           m["exact_horizon"]==60 and m["friction_bps"]==200)
    r={"physical_cohort_ready":ready,"independent_tokens":i["independent_tokens"],
       "physical_history_rows":i["physical_history_rows"],
       "frozen_thesis":FROZEN_THESIS,
       "state":"READY_FOR_EXACT_PHYSICAL_ECONOMIC_MATURITY" if ready else "INSUFFICIENT_PHYSICAL_SUPPORT",
       "profitability_claimed":False,"read_only":True,"execution_authority":False}
    print("[SSI-015A]",r);return r
