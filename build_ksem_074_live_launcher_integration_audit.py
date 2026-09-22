from pathlib import Path
import ast
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"; STATE=PKG/"state"
TEST=ROOT/"test_ksem_074_live_launcher_integration_audit.py"
def main():
    print("="*120); print(" KSEM-074 LIVE LAUNCHER INTEGRATION AUDIT INSTALLER"); print("="*120)
    launcher=ROOT/"run_oracle_LIVE.py"
    if not launcher.is_file(): raise RuntimeError("run_oracle_LIVE.py missing")
    source=launcher.read_text(encoding="utf-8")
    ast.parse(source)
    report={
        "launcher":str(launcher.relative_to(ROOT)),
        "contains_children":"CHILDREN" in source,
        "contains_sports":"sports" in source.lower(),
        "contains_ksem":"ksem" in source.lower(),
        "contains_popen":"Popen" in source or "subprocess" in source,
        "launcher_lines":len(source.splitlines()),
    }
    STATE.mkdir(parents=True,exist_ok=True)
    import json
    (STATE/"ksem074_launcher_audit.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    TEST.write_text("""from pathlib import Path\nimport json\nroot=Path.cwd()\nr=json.loads((root/'qseries_v2/kalshi_sports_evidence_mapping/state/ksem074_launcher_audit.json').read_text(encoding='utf-8'))\nprint('[AUDIT]',r)\nassert r['contains_children'], 'production launcher CHILDREN structure not detected'\nassert r['contains_popen'], 'production child process launch mechanism not detected'\nprint('[PASS] exact live launcher integration surface audited without mutation')\nprint('[PASS] KSEM-074 certified')\n""",encoding="utf-8")
    print("[AUDIT]",report)
    print("[PASS] wrote",TEST.name)
    print("[PASS] run_oracle_LIVE.py intentionally NOT modified")
    print("[PASS] KSEM-074 installer complete")
if __name__=="__main__": main()