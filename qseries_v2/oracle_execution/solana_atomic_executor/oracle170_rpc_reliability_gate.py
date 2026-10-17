
import argparse, json, re
from pathlib import Path

OUT = Path("runtime_state/oracle/oracle_live_execution/ORACLE170_RPC_RELIABILITY.json")

def audit(text):
    lines = text.splitlines()
    ws = sum("WS_RECOVER" in x and ("429" in x or "Too Many Requests" in x) for x in lines)
    http = sum("429" in x and "WS_RECOVER" not in x for x in lines)
    hb = [x for x in lines if "[CANONICAL_HEARTBEAT]" in x]
    eps = []
    for x in hb:
        m = re.search(r"eps=([0-9.]+)", x)
        if m:
            eps.append(float(m.group(1)))
    bad = not hb or ws > 0 or http > 0 or (eps and min(eps) < 0.5)
    return {
        "build": "ORACLE170",
        "websocket_429": ws,
        "non_websocket_429": http,
        "heartbeat_samples": len(hb),
        "min_events_per_second": min(eps) if eps else None,
        "transport_certified": not bad,
        "execution_authorized": False,
        "reason": "HOLD_RPC_THROTTLED_OR_INSUFFICIENT" if bad else "HEALTH_WINDOW_ONLY_NOT_EXECUTION_CERTIFICATION"
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True)
    args = p.parse_args()
    log = Path(args.log)
    if not log.is_file():
        raise SystemExit("[HOLD] LOG_FILE_NOT_FOUND")
    result = audit(log.read_text(encoding="utf-8", errors="replace"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("[ORACLE170]", result["reason"], "ws429=", result["websocket_429"],
          "http429=", result["non_websocket_429"])
    print("[REPORT]", OUT)

if __name__ == "__main__":
    main()
