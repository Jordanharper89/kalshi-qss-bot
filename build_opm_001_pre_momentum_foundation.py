from pathlib import Path
import py_compile

R=Path.cwd()
P=R/"qseries_v2"/"oracle_pre_momentum"
P.mkdir(parents=True,exist_ok=True)
(P/"__init__.py").touch()

M='''SCHEMA_VERSION="OPM-001"
MISSION="independent reality -> future Kalshi price path"
HORIZONS_SECONDS=(5,15,30,60,120,300)
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
'''
(P/"opm_001_foundation.py").write_text(M,encoding="utf-8")

T='''from qseries_v2.oracle_pre_momentum.opm_001_foundation import *
assert HORIZONS_SECONDS==(5,15,30,60,120,300)
assert not PROBABILITY_ENABLED
assert not DIRECTION_ENABLED
assert not PUBLICATION_ALLOWED
assert not EXECUTION_AUTHORITY
print("[PASS] OPM independent pre-momentum subsystem established")
print("[PASS] 5/15/30/60/120/300 second path horizons declared")
print("[PASS] prediction publication and execution remain disabled")
print("[PASS] OPM-001 foundation certified")
'''
t=R/"test_opm_001_pre_momentum_foundation.py"
t.write_text(T,encoding="utf-8")
py_compile.compile(str(t),doraise=True)
print("[PASS] wrote OPM-001 foundation + test")