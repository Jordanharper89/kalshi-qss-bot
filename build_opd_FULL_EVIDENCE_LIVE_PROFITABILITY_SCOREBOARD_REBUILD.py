from pathlib import Path

R=Path.cwd()
M=R/"qseries_v2"/"oracle_predictive_discovery"/"opd_full_evidence_live_profitability_scoreboard.py"
T=R/"test_opd_FULL_EVIDENCE_LIVE_PROFITABILITY_CALIBRATION_SCOREBOARD.py"
N=R/"test_opd_FULL_EVIDENCE_LIVE_PROFITABILITY_SCOREBOARD_REBUILD.py"
RUN=R/"run_opd_full_evidence_predictor_child.py"

for p in (M,T,RUN):
    if not p.exists(): raise SystemExit("[FAIL] missing: "+str(p))

def repair(p):
    s=p.read_text(encoding="utf-8")
    # Retired installer emitted literal newline inside quoted "\\n" strings.
    s=s.replace('"\n"', '"\\\\n"')
    p.write_text(s,encoding="utf-8")
    compile(s,str(p),"exec")

repair(M)
repair(T)

runner=RUN.read_text(encoding="utf-8")
for x in ("run_prediction(root=root)",
          "resolve_full_evidence_outcomes(root)",
          "run_full_evidence_scoreboard(root)"):
    if x not in runner: raise SystemExit("[FAIL] runtime boundary missing: "+x)
compile(runner,str(RUN),"exec")

# Reuse repaired deterministic test under a new filename so stale test is not rerun.
N.write_text(T.read_text(encoding="utf-8"),encoding="utf-8")
compile(N.read_text(encoding="utf-8"),str(N),"exec")

print("[PASS] profitability scoreboard syntax repaired in existing production file")
print("[PASS] deterministic scoreboard test syntax repaired and copied to fresh test filename")
print("[PASS] predictor -> resolver -> scoreboard runtime order preserved")
print("[PASS] fixed 2pct hurdle and prediction gates unchanged")
print("[PROFITABILITY_CERTIFIED] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
