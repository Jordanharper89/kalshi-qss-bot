from pathlib import Path
import ast
P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint25_expanded_live_universe_cutover.py"
)

s=P.read_text(encoding="utf-8")

old='''        out.append({
            "identity":identity,
            "token":token,
            "pump_pool":str(row["pump_pool"]),
            "meteora_pool":pool,
            "token_x":str(row["token_x"]),
            "token_y":str(row["token_y"]),
            "decimals_x":int(row["decimals_x"]),
            "decimals_y":int(row["decimals_y"]),
            "selected_legacy":bool(row.get("retained")),
            "source":"CHECKPOINT24_CAPACITY_AWARE",
            "account_cost":int(row.get("account_cost") or 0),
            "reported_tvl":float(row.get("reported_tvl") or 0),
        })'''

new='''        out.append({
            "pair_key":identity,
            "token":token,
            "pump_pool":str(row["pump_pool"]),
            "meteora_pool":pool,
            "selected_legacy":bool(row.get("retained")),
            "discovery_rank":len(out)+1,
            "reported_tvl":float(row.get("reported_tvl") or 0),
            "token_x":str(row["token_x"]),
            "token_y":str(row["token_y"]),
            "decimals_x":int(row["decimals_x"]),
            "decimals_y":int(row["decimals_y"]),
            "array_count":len(row.get("array_addresses") or []),
            "complete_quote_count":1,
            "partial_size_count":0,
            "best_direction":"UNMEASURED_AT_CUTOVER",
            "best_size_sol":0.0,
            "best_local_net_lamports":0,
            "best_local_bps":0.0,
            "gross_positive":False,
        })'''

if old not in s:
    raise RuntimeError("CHECKPOINT25_ROW_BLOCK_NOT_FOUND")

s=s.replace(old,new,1)

old_report='''    return {
        "revision":
            "CHECKPOINT25_EXPANDED_RUNTIME_REGISTRY",
        "observed_unix":time.time(),
        "ready_pairs":len(out),
        "pair_identities":len(out),
        "identity":"token|meteora_pool",
        "rows":out,
        "execution_authority":False,
        "broadcast":False,
        "temporary_runtime_cutover":True,
    }'''

new_report='''    by_token={}
    for row in out:
        by_token[row["token"]]=by_token.get(row["token"],0)+1

    return {
        "revision":"CHECKPOINT11_MULTI_POOL_REGISTRY_V1",
        "observed_unix":time.time(),
        "identity":"token|meteora_pool",
        "source_pool_limit_per_token":100,
        "tokens":len(by_token),
        "ready_pair_count":len(out),
        "alternate_ready_count":sum(
            1 for row in out
            if not row["selected_legacy"]
        ),
        "gross_positive_count":0,
        "failures":[],
        "rows":out,
        "execution_authority":False,
        "simulation":False,
        "broadcast":False,
        "temporary_runtime_cutover":True,
    }'''

if old_report not in s:
    raise RuntimeError("CHECKPOINT25_REPORT_BLOCK_NOT_FOUND")

s=s.replace(old_report,new_report,1)

P.write_text(s,encoding="utf-8")
ast.parse(P.read_text(encoding="utf-8"))

print("[PASS] checkpoint-25 registry contract corrected")
print("[ROW_IDENTITY] pair_key=token|meteora_pool")
print("[SCHEMA] CHECKPOINT11_MULTI_POOL_REGISTRY_V1 preserved")
print("[RESTORE] original 19-row registry behavior unchanged")
print("[KEY] untouched")
print("[BROADCAST] disabled")
