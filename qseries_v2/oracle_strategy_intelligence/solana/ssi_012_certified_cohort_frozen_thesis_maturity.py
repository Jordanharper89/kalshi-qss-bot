from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_271_solana_historical_experience_formation import build_solana_historical_experiences
import inspect

TOKENS=(
"7AaRtPFz8BFHgCTt55VwPW6ErYULXzjd9fd3Arbdpump",
"A38S7ywWTSQHDU6dQBZVonmezf4tdtxhuanKAiz7DSmW",
"FstQsxUszLcr6VDsq4e8msQ5t6HFU68RNGwRsJ8a7R1g",
"2TFioVNNgnWiPmBVK83h3NSdffQVdJb3P97poyTgpump",
"BLGM7XgLpm5uUGJXHTGGQvNYk5jeKSr9kfCdqyq3GR8c",
)
FROZEN_THESIS={"horizon":60,"target":0.10,"stop":0.05,
"condition":("order_flow","BUY_PRESSURE"),"friction_bps":200}

def audit(root=None):
    rows=[]
    for token in TOKENS:
        h=tuple(read_pinned_pool_history(token,root=root,limit=4096))
        e=tuple(build_solana_historical_experiences(h))
        rows.append({"token":token,"history":len(h),"experiences":len(e),
                     "sample_type":type(e[0]).__name__ if e else None,
                     "sample_repr":repr(e[0])[:2000] if e else None})
    r={"tokens":TOKENS,"frozen_thesis":FROZEN_THESIS,
       "episodes":tuple(rows),"independent_tokens":len(set(TOKENS)),
       "experience_signature":str(inspect.signature(build_solana_historical_experiences)),
       "read_only":True,"execution_authority":False}
    print("[SSI-012A]",r)
    return r
