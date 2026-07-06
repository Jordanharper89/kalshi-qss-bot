"""
build_core_005_oracle_api.py
CORE-005 Oracle API Layer Installer
"""

from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
CORE = ROOT / "qseries_v2" / "core"

def backup(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = path.with_suffix(path.suffix + f".bak_{stamp}")
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup(path)
    path.write_text(text, encoding="utf-8")
    print(f"[OK] Wrote {path.relative_to(ROOT)}")

api_code = '''"""
CORE-005 Oracle API Layer
"""

from .service_registry import service_registry
from .event_bus import event_bus

class OracleAPI:

    def get_service(self, service_id):
        return service_registry.get(service_id)

    def publish(self, event_name, payload=None):
        event_bus.publish(event_name, payload)

    def subscribe(self, event_name, callback):
        event_bus.subscribe(event_name, callback)

oracle_api = OracleAPI()
'''

test_code = '''from qseries_v2.core.oracle_api import oracle_api

events=[]

def handler(data):
    events.append(data)

oracle_api.subscribe("api_test", handler)
oracle_api.publish("api_test", {"status":"ok"})

assert events[0]["status"]=="ok"

print("[PASS] CORE-005 Oracle API Layer")
'''

print("="*40)
print(" CORE-005 INSTALLER")
print(" Oracle API Layer")
print("="*40)

write(CORE/"oracle_api.py", api_code)
write(ROOT/"test_core_005_oracle_api.py", test_code)

print()
print("[DONE] CORE-005 installed")
print()
print("Run:")
print("python test_core_005_oracle_api.py")