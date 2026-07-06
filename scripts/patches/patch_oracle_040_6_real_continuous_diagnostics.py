from pathlib import Path
from datetime import datetime

path = Path("oracle_continuous_intelligence.py")

if not path.exists():
    raise FileNotFoundError("oracle_continuous_intelligence.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

old = '''def diagnostics():
    result = run_cycle(opportunities=[
        {
            "ticker": "TEST-CONTINUOUS-1",
            "title": "Continuous Intelligence Test",
            "side": "YES",
            "edge": 8.6,
            "confidence": 92,
            "fair_value": 0.69,
            "market_price": 0.59,
            "volume": 42000,
            "age_seconds": 35,
            "providers": ["oracle", "cache", "research"],
        }
    ])

    return {
        "module": "oracle_continuous_intelligence",
        "status": "ok",
        "cycle_result": result,
        "pipeline_status": status(),
    }
'''

new = '''def diagnostics():
    """
    ORACLE-040.6:
    Diagnostics now tests the real live Market Intelligence source,
    not the old hardcoded sample opportunity.
    """
    result = run_cycle(opportunities=None)

    return {
        "module": "oracle_continuous_intelligence",
        "status": "ok",
        "cycle_result": result,
        "pipeline_status": status(),
    }
'''

if old not in text:
    raise RuntimeError("Could not find old diagnostics block.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-040.6 INSTALLED")
print(" Real Continuous Diagnostics")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python oracle_continuous_intelligence.py")