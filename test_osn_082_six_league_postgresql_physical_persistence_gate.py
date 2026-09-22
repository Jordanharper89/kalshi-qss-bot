
from pathlib import Path
from qseries_v2.oracle_source_network.certification.six_league_postgresql_persistence_gate import run_gate

result,state=run_gate(root=Path.cwd())
print("[PERSISTENCE_GATE]",result)
assert result.committed_or_present==6
assert result.exact_readback_verified==6
assert result.single_writer=="OPH-019"
assert result.gate_ready is True
assert result.execution_authority is False
print("[STATE]",state)
print("[PASS] six-league PostgreSQL physical persistence gate certified")
