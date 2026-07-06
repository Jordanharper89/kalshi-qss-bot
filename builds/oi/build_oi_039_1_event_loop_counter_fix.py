from pathlib import Path

ROOT = Path.cwd()
ENGINE = ROOT / "qseries_v2" / "oracle_intelligence" / "event_driven_learning_loop.py"

if not ENGINE.exists():
    raise FileNotFoundError("Missing OI-039 event_driven_learning_loop.py")

text = ENGINE.read_text(encoding="utf-8")

old = '"events_processed": self.events_processed + 1,'
new = '"events_processed": self.events_processed,'

if old not in text:
    print("[WARN] Counter line already fixed or not found")
else:
    text = text.replace(old, new)

ENGINE.write_text(text, encoding="utf-8")

print("========================================")
print(" OI-039.1 INSTALLER")
print(" Event Loop Counter Fix")
print("========================================")
print(f"[OK] Patched {ENGINE}")
print("")
print("[DONE] OI-039.1 installed")
print("")
print("Run:")
print("python test_oi_039_event_driven_learning_loop.py")