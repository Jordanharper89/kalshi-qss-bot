from qseries_v2.core.oracle_api import oracle_api

events=[]

def handler(data):
    events.append(data)

oracle_api.subscribe("api_test", handler)
oracle_api.publish("api_test", {"status":"ok"})

assert events[0]["status"]=="ok"

print("[PASS] CORE-005 Oracle API Layer")
