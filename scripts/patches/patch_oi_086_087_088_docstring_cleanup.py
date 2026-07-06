from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
INIT = PKG / "__init__.py"

FILES_TO_FIX = [
    PKG / "market_influence_graph_engine.py",
    PKG / "market_regime_transition_graph_engine.py",
    PKG / "systemic_risk_contagion_engine.py",
]

print("========================================")
print(" OI-086/087/088 FIX PATCH")
print(" Escaped Docstring Cleanup")
print("========================================")

for path in FILES_TO_FIX:
    if not path.exists():
        print(f"[SKIP] Missing {path}")
        continue

    text = path.read_text(encoding="utf-8")
    fixed = text.replace(r'\"\"\"', '"""')

    if fixed != text:
        path.write_text(fixed, encoding="utf-8")
        print(f"[OK] Fixed escaped docstrings in {path}")
    else:
        print(f"[OK] No escaped docstrings found in {path}")

# Make sure imports exist once.
required_imports = [
    "from .market_influence_graph_engine import market_influence_graph_engine\n",
    "from .market_regime_transition_graph_engine import market_regime_transition_graph_engine\n",
    "from .systemic_risk_contagion_engine import systemic_risk_contagion_engine\n",
]

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

for line in required_imports:
    if line not in init_text:
        init_text = init_text.rstrip() + "\n" + line

INIT.write_text(init_text.rstrip() + "\n", encoding="utf-8")
print(f"[OK] Verified {INIT}")

print()
print("[DONE] OI-086/087/088 cleanup complete")
print()
print("Run:")
print("python test_oi_086_market_influence_graph_engine.py")
print("python test_oi_087_market_regime_transition_graph_engine.py")
print("python test_oi_088_systemic_risk_contagion_engine.py")
