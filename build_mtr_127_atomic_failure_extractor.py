from pathlib import Path

p=Path("mtr_127_atomic_failure_extractor.py")

p.write_text(r'''from __future__ import annotations
import json
from pathlib import Path

SRC=Path("mtr_126_official_sdk_atomic_swap2_cutover.json")
OUT=Path("mtr_127_atomic_failure_extractor.json")

def main():
    print("[MTR-127] START",flush=True)
    print("[SCOPE] read-only MTR-126 atomic failure extraction",flush=True)

    if not SRC.is_file():
        raise RuntimeError("MTR126_REPORT_MISSING")

    j=json.loads(SRC.read_text(encoding="utf-8"))
    rows=j.get("atomic_rows") or []

    out=[]
    for n,r in enumerate(rows,1):
        item={
            "n":n,
            "route":r.get("route"),
            "slot":r.get("slot"),
            "direction":r.get("direction"),
            "local_bps":r.get("local_bps"),
            "compiled":r.get("compiled"),
            "candidate":r.get("candidate"),
            "bytes":r.get("bytes"),
            "sim_err":r.get("sim_err"),
            "sim_units":r.get("sim_units"),
            "pump_seen":r.get("pump_program_seen"),
            "meteora_seen":r.get("meteora_program_seen"),
            "error":r.get("error"),
            "compile_attempts":r.get("compile_attempts"),
        }
        out.append(item)

        print(
            "[MTR127_ROW] n=%d bytes=%s err=%s error=%s "
            "units=%s pump=%s meteora=%s"
            %(
                n,
                item["bytes"],
                item["sim_err"],
                item["error"],
                item["sim_units"],
                item["pump_seen"],
                item["meteora_seen"],
            ),
            flush=True,
        )

        for a in item["compile_attempts"] or []:
            if not a.get("ok"):
                print(
                    "[MTR127_COMPILE_FAIL] candidate=%s bytes=%s error=%s"
                    %(a.get("candidate"),a.get("bytes"),a.get("error")),
                    flush=True,
                )

    result={
        "mtr":"MTR-127",
        "source":str(SRC),
        "atomic_attempts":j.get("atomic_attempts"),
        "compiled":j.get("compiled"),
        "simulated":j.get("simulated"),
        "atomic_pass":j.get("atomic_pass"),
        "rows":out,
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(result,indent=2,sort_keys=True,default=str),
        encoding="utf-8",
    )

    print(
        "[SUMMARY] attempts=%s compiled=%s simulated=%s atomic_pass=%s"
        %(result["atomic_attempts"],result["compiled"],
          result["simulated"],result["atomic_pass"]),
        flush=True,
    )
    print("[RESULT] MTR126_NEXT_BLOCKER_EXTRACTED",flush=True)
    print("[OUTPUT] "+str(OUT),flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)
    print("[MTR-127] COMPLETE",flush=True)

if __name__=="__main__":
    main()
''',encoding="utf-8")

print("[BUILD] wrote",p)
print("[BUILD] MTR-126 atomic failure extractor")
print("[SCOPE] report-only; no RPC; no transaction")