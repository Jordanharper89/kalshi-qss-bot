from pathlib import Path
from qseries_v2.oracle_continuous_reasoning.ocr_013_continuous_reasoning_loop import run_continuous_reasoning_cycle

if __name__=="__main__":
    print("="*72);print(" OCR-015 PHYSICAL CONTINUOUS REASONING CYCLE VERIFICATION");print("="*72)
    s=run_continuous_reasoning_cycle(Path.cwd(),limit=25,progress=lambda x:print(x,flush=True))
    print("[SUMMARY]",s)
    if s.idle:
        print("[PASS] No unprocessed observations available; cursor/runtime path healthy")
    else:
        if not s.cursor_advanced or s.ois_projections<1:raise SystemExit("[FAIL] reasoning cycle incomplete")
        print("[PASS] New observations processed through OSR and OIS projection with cursor advancement")
    print("[DONE] OCR-015 PHYSICAL CONTINUOUS REASONING CYCLE VERIFIED")
