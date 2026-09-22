from qseries_v2.oracle_adapters.independent.oad_411_solana_production_catchup_physical_gate import run_production_catchup_physical_gate
x=run_production_catchup_physical_gate(max_cycles=2,progress=lambda *a:print("[LIVE]",*a))
print(x)
