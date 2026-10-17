
import json
from pathlib import Path

STATE = Path("runtime_state/oracle/oracle_live_execution")

def get(name):
    path = STATE / name
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}

def decide(transport, packet):
    t = transport.get("transport_certified") is True
    p = packet.get("packet_certified") is True
    return {
        "build": "ORACLE172",
        "transport_window_pass": t,
        "native_packet_pass": p,
        "two_leg_signed_sim_pass": False,
        "net_profit_reconciliation_pass": False,
        "execution_authorized": False,
        "result": (
            "HOLD_SIMULATION_AND_RECONCILIATION_UNCERTIFIED"
            if t and p
            else "HOLD_TRANSPORT_OR_NATIVE_PACKET_UNCERTIFIED"
        )
    }

def main():
    report = decide(
        get("ORACLE170_RPC_RELIABILITY.json"),
        get("ORACLE171_NATIVE_PACKET_GATE.json")
    )
    STATE.mkdir(parents=True, exist_ok=True)
    out = STATE / "ORACLE172_EXECUTION_READINESS.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[ORACLE172]", report["result"], "broadcast=FALSE")
    print("[REPORT]", out)

if __name__ == "__main__":
    main()
