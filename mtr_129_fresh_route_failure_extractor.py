from __future__ import annotations
import json
from pathlib import Path

SRC=Path("mtr_128_underlying_atomic_preflight.json")
OUT=Path("mtr_129_fresh_route_failure_extractor.json")

def main():
    print("[MTR-129] START",flush=True)
    print("[SCOPE] MTR-128 precompile failure extraction only",flush=True)

    if not SRC.is_file():
        raise RuntimeError("MTR128_UNDERLYING_REPORT_MISSING")

    j=json.loads(SRC.read_text(encoding="utf-8"))
    rows=j.get("atomic_rows") or []

    extracted=[]

    for n,r in enumerate(rows,1):
        item={
            "n":n,
            "route":r.get("route"),
            "token":r.get("token"),
            "direction":r.get("direction"),
            "slot":r.get("slot"),
            "pre_sim_bps":r.get("pre_sim_bps"),
            "compiled":r.get("compiled"),
            "bytes":r.get("bytes"),
            "sim_err":r.get("sim_err"),
            "error":r.get("error"),
            "compile_attempts":r.get("compile_attempts"),
        }

        extracted.append(item)

        print(
            "[MTR129_ROW] n=%d token=%s dir=%s bps=%s "
            "compiled=%s bytes=%s sim_err=%s error=%s"
            %(
                n,
                item["token"],
                item["direction"],
                item["pre_sim_bps"],
                item["compiled"],
                item["bytes"],
                item["sim_err"],
                item["error"],
            ),
            flush=True,
        )

        for a in item["compile_attempts"] or []:
            print(
                "[MTR129_COMPILE] candidate=%s ok=%s bytes=%s error=%s"
                %(
                    a.get("candidate"),
                    a.get("ok"),
                    a.get("bytes"),
                    a.get("error"),
                ),
                flush=True,
            )

    out={
        "mtr":"MTR-129",
        "atomic_attempts":j.get("atomic_attempts"),
        "compiled":j.get("compiled"),
        "simulated":j.get("simulated"),
        "atomic_pass":j.get("atomic_pass"),
        "rows":extracted,
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(out,indent=2,sort_keys=True,default=str),
        encoding="utf-8",
    )

    print(
        "[SUMMARY] attempts=%s compiled=%s simulated=%s atomic_pass=%s"
        %(
            out["atomic_attempts"],
            out["compiled"],
            out["simulated"],
            out["atomic_pass"],
        ),
        flush=True,
    )

    print("[RESULT] MTR128_PRECOMPILE_BLOCKER_EXTRACTED",flush=True)
    print("[OUTPUT] "+str(OUT),flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)
    print("[MTR-129] COMPLETE",flush=True)

if __name__=="__main__":
    main()
