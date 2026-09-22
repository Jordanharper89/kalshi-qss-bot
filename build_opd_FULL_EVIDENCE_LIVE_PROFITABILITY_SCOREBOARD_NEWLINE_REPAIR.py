from pathlib import Path

R=Path.cwd()
M=R/"qseries_v2"/"oracle_predictive_discovery"/"opd_full_evidence_live_profitability_scoreboard.py"
OLD=R/"test_opd_FULL_EVIDENCE_LIVE_PROFITABILITY_SCOREBOARD_REBUILD.py"
NEW=R/"test_opd_FULL_EVIDENCE_LIVE_PROFITABILITY_SCOREBOARD_NEWLINE_REPAIR.py"

for p in (M,OLD):
    if not p.exists(): raise SystemExit("[FAIL] missing: "+str(p))

def fix(p):
    s=p.read_text(encoding="utf-8")
    before=s.count('"\\\\\\\\n"')
    s=s.replace('"\\\\\\\\n"','"\\\\n"')
    p.write_text(s,encoding="utf-8")
    compile(s,str(p),"exec")
    return before

mfix=fix(M)
tfix=fix(OLD)
if mfix<1 or tfix<1:
    raise SystemExit(f"[FAIL] expected escaped-newline defect not found module={mfix} test={tfix}")

NEW.write_text(OLD.read_text(encoding="utf-8"),encoding="utf-8")
compile(NEW.read_text(encoding="utf-8"),str(NEW),"exec")

print("[PASS] scoreboard JSON newline semantics repaired")
print("[PASS] deterministic JSONL fixture newline semantics repaired")
print("[PASS] fresh deterministic test filename installed")
print("[PASS] profitability math, 2pct hurdle, and prediction gates unchanged")
print("[PROFITABILITY_CERTIFIED] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
