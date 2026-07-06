"""
build_core_003_event_bus.py
CORE-003 Universal Event Bus Installer
"""

from pathlib import Path
from datetime import datetime
ROOT=Path.cwd()
CORE=ROOT/"qseries_v2"/"core"

def backup(path):
    if path.exists():
        stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        bak=path.with_suffix(path.suffix+f".bak_{stamp}")
        bak.write_text(path.read_text(encoding="utf-8"),encoding="utf-8")

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): backup(path)
    path.write_text(text,encoding="utf-8")
    print(f"[OK] Wrote {path.relative_to(ROOT)}")

print("="*40)
print(" CORE-003 INSTALLER")
print(" Universal Event Bus")
print("="*40)

event_bus_code = """
from collections import defaultdict
class EventBus:
    def __init__(self):
        self._subs=defaultdict(list)
    def subscribe(self,event,cb):
        self._subs[event].append(cb)
    def unsubscribe(self,event,cb):
        if cb in self._subs[event]: self._subs[event].remove(cb)
    def publish(self,event,payload=None):
        for cb in list(self._subs[event]):
            cb(payload)
event_bus=EventBus()
"""
write(CORE/"event_bus.py", event_bus_code)

test_code="""from qseries_v2.core.event_bus import event_bus
out=[]
def h(d):
    out.append(d)
event_bus.subscribe("demo",h)
event_bus.publish("demo",{"status":"ok"})
assert out[0]["status"]=="ok"
print("[PASS] CORE-003 Event Bus")
"""
write(ROOT/"test_core_003_event_bus.py", test_code)
print("\n[DONE] CORE-003 installed")
print("Run:")
print("python test_core_003_event_bus.py")