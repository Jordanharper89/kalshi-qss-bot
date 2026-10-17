
import json
from pathlib import Path

STATE = Path("runtime_state/oracle/oracle_live_execution")
SRC = STATE / "ORACLE169_NATIVE_COMPILE_EVIDENCE.jsonl"
OUT = STATE / "ORACLE171_NATIVE_PACKET_GATE.json"

def evaluate(rows):
    found = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        direction = r.get("direction")
        order = any(
            isinstance(c, dict)
            and c.get("ata_first_two") is True
            and c.get("pump_legs") == 1
            and c.get("meteora_legs") == 1
            and c.get("swap_order") == direction
            for c in (r.get("candidates") or [])
        )
        size = r.get("packet_bytes")
        valid = (
            r.get("compiler_pass") is True
            and type(size) is int
            and 100 <= size <= 1232
            and r.get("amount_050_sol") is True
            and order
            and direction in ("PUMP_TO_METEORA", "METEORA_TO_PUMP")
        )
        if valid:
            found.append({"direction": direction, "packet_bytes": size})
    return {
        "build": "ORACLE171",
        "packet_certified": bool(found),
        "valid_packets": found[-10:],
        "reason": "PASS_REAL_NATIVE_PACKET" if found else "HOLD_NO_CERTIFIED_REAL_PACKET",
        "signed_simulation_certified": False,
        "execution_authorized": False
    }

def main():
    records = []
    if SRC.is_file():
        for line in SRC.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    report = evaluate(records)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[ORACLE171]", report["reason"], "valid_packets=", len(report["valid_packets"]))
    print("[REPORT]", OUT)

if __name__ == "__main__":
    main()
