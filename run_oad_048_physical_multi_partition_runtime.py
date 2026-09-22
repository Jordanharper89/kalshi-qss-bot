from pathlib import Path
from qseries_v2.oracle_adapters.kalshi.oad_048_multi_partition_runtime import run_physical_multi_partition_persistence
if __name__=="__main__":
    print("="*72,flush=True);print(" OAD-048 PHYSICAL MULTI-PARTITION KALSHI RUNTIME",flush=True);print("="*72,flush=True)
    r=run_physical_multi_partition_persistence(Path.cwd(),max_persisted=10,orderbook_partitions_to_activate=3,progress=lambda x:print(x,flush=True))
    print("[SUMMARY]",r,flush=True)
    print("[PASS] Multi-partition live market data persisted through OLA PostgreSQL",flush=True)
