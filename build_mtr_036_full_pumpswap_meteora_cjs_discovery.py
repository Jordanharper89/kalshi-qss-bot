from pathlib import Path
src=Path("mtr_035_full_pumpswap_meteora_intersection_discovery.js")
dst=Path("mtr_036_full_pumpswap_meteora_cjs_discovery.cjs")
if not src.exists():
    raise SystemExit("[FAIL] missing MTR-035 generated JS; run its installer first")
text=src.read_text(encoding="utf-8")
old='import fs from "fs";\nimport {Connection,PublicKey} from "@solana/web3.js";\nimport DLMM from "@meteora-ag/dlmm";'
new='const fs = require("fs");\nconst {Connection,PublicKey} = require("@solana/web3.js");\nconst _dlmm = require("@meteora-ag/dlmm");\nconst DLMM = _dlmm.default || _dlmm.DLMM || _dlmm;'
if old not in text:
    raise SystemExit("[FAIL] MTR-035 import block not found; refusing speculative rewrite")
text=text.replace(old,new,1).replace("[MTR-035] START","[MTR-036] START",1)
text=text.replace('"schema":"MTR-035"','"schema":"MTR-036"',1)
text=text.replace('"mtr_035_candidates.json"','"mtr_036_candidates.json"')
text=text.replace("[OUTPUT] mtr_035_candidates.json","[OUTPUT] mtr_036_candidates.json")
text=text.replace("[MTR-035] COMPLETE","[MTR-036] COMPLETE")
text=text.replace("[MTR-035] FAIL","[MTR-036] FAIL")
dst.write_text(text,encoding="utf-8")
print(f"[BUILD] wrote {dst}")
print("[BUILD] CJS loader boundary only; discovery logic preserved")
print("[SCOPE] no signing; no sending; canonical executor untouched")
