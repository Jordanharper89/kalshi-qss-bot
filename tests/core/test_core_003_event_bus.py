from qseries_v2.core.event_bus import event_bus
out=[]
def h(d):
    out.append(d)
event_bus.subscribe("demo",h)
event_bus.publish("demo",{"status":"ok"})
assert out[0]["status"]=="ok"
print("[PASS] CORE-003 Event Bus")
