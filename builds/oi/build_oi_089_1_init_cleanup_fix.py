from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
INIT = PKG / "__init__.py"

print("========================================")
print(" OI-089.1 INSTALLER")
print(" Oracle Intelligence Init Cleanup Fix")
print("========================================")

if not INIT.exists():
    raise FileNotFoundError(f"Missing {INIT}")

text = INIT.read_text(encoding="utf-8")

# Fix literal backslash-n characters accidentally written by OI-089/OI-090/OI-091 installers.
text = text.replace("\\n", "\n")

# Remove duplicate blank/import lines while preserving order.
lines = text.splitlines()
clean_lines = []
seen_imports = set()

for line in lines:
    stripped = line.strip()

    if not stripped:
        if clean_lines and clean_lines[-1] != "":
            clean_lines.append("")
        continue

    if stripped.startswith("from .") and " import " in stripped:
        if stripped in seen_imports:
            continue
        seen_imports.add(stripped)
        clean_lines.append(stripped)
    else:
        clean_lines.append(line.rstrip())

required_imports = [
    "from .market_influence_graph_engine import market_influence_graph_engine",
    "from .market_regime_transition_graph_engine import market_regime_transition_graph_engine",
    "from .systemic_risk_contagion_engine import systemic_risk_contagion_engine",
    "from .cascade_severity_ranking_engine import cascade_severity_ranking_engine",
    "from .shock_path_trace_engine import shock_path_trace_engine",
    "from .market_fragility_score_engine import market_fragility_score_engine",
]

existing = set(line.strip() for line in clean_lines)
for import_line in required_imports:
    if import_line not in existing:
        clean_lines.append(import_line)
        existing.add(import_line)

INIT.write_text("\n".join(clean_lines).rstrip() + "\n", encoding="utf-8")
print(f"[OK] Cleaned {INIT}")

# Quick syntax compile for affected modules.
affected = [
    PKG / "cascade_severity_ranking_engine.py",
    PKG / "shock_path_trace_engine.py",
    PKG / "market_fragility_score_engine.py",
    INIT,
]

import py_compile

for path in affected:
    if path.exists():
        py_compile.compile(str(path), doraise=True)
        print(f"[OK] Syntax verified {path}")
    else:
        print(f"[WARN] Missing {path}")

print()
print("[DONE] OI-089.1 cleanup installed")
print()
print("Run:")
print("python test_oi_089_cascade_severity_ranking_engine.py")
print("python test_oi_090_shock_path_trace_engine.py")
print("python test_oi_091_market_fragility_score_engine.py")
