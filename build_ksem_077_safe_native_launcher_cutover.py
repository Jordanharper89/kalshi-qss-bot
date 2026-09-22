from pathlib import Path
import ast, hashlib, json, shutil
ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
LAUNCHER=ROOT/"run_oracle_LIVE.py"
BACKUP=ROOT/"run_oracle_LIVE.pre_ksem077.py"
TEST=ROOT/"test_ksem_077_safe_native_launcher_cutover.py"
KEY="ksem_mapping"
RUNNER="run_ksem_live_mapping.py"

def sha(text): return hashlib.sha256(text.encode()).hexdigest()

def children_from(src):
    tree=ast.parse(src)
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in node.targets):
            value=ast.literal_eval(node.value)
            if not isinstance(value,dict): raise RuntimeError("CHILDREN_NOT_DICT")
            return value
    raise RuntimeError("CHILDREN_ASSIGNMENT_NOT_FOUND")

def patch(src):
    if f'"{KEY}"' in src or f"'{KEY}'" in src:
        return src
    marker='    "sports": "run_osn_sports_continuous_runtime.py",'
    if marker not in src:
        raise RuntimeError("EXACT_SPORTS_CHILD_MARKER_NOT_FOUND__NO_PATCH_PERFORMED")
    return src.replace(marker,marker+f'\n    "{KEY}": "{RUNNER}",',1)

def main():
    print("="*120); print(" KSEM-077 SAFE NATIVE LAUNCHER CUTOVER INSTALLER"); print("="*120)
    if not LAUNCHER.is_file(): raise RuntimeError("run_oracle_LIVE.py missing")
    if not (ROOT/RUNNER).is_file(): raise RuntimeError(f"{RUNNER} missing")
    contract_path=STATE/"ksem076_live_children_contract.json"
    if not contract_path.is_file(): raise RuntimeError("KSEM-076 contract missing")
    contract=json.loads(contract_path.read_text(encoding="utf-8"))
    original=LAUNCHER.read_text(encoding="utf-8")
    current_hash=sha(original)
    expected=contract["launcher_sha256"]
    if current_hash!=expected and KEY not in children_from(original):
        raise RuntimeError(f"LAUNCHER_HASH_CHANGED_SINCE_KSEM076 expected={expected} actual={current_hash}")
    if not BACKUP.exists():
        shutil.copy2(LAUNCHER,BACKUP)
        print("[PASS] rollback backup written:",BACKUP.name)
    updated=patch(original)
    ast.parse(updated)
    LAUNCHER.write_text(updated,encoding="utf-8")
    reread=LAUNCHER.read_text(encoding="utf-8")
    children=children_from(reread)
    if children.get(KEY)!=RUNNER:
        shutil.copy2(BACKUP,LAUNCHER)
        raise RuntimeError("CUTOVER_VERIFICATION_FAILED__ROLLBACK_RESTORED")
    report={"schema_version":"KSEM-077","before_sha256":current_hash,"after_sha256":sha(reread),
            "backup":BACKUP.name,"child_key":KEY,"child_runner":RUNNER,
            "children_count":len(children),"execution_authority":False}
    STATE.mkdir(parents=True,exist_ok=True)
    (STATE/"ksem077_native_launcher_cutover.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    TEST.write_text("""from pathlib import Path\nimport ast,json\nroot=Path.cwd(); src=(root/'run_oracle_LIVE.py').read_text(encoding='utf-8'); tree=ast.parse(src)\nchildren=None\nfor n in tree.body:\n    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHILDREN' for t in n.targets): children=ast.literal_eval(n.value); break\nprint('[CHILDREN]',children)\nassert children['ksem_mapping']=='run_ksem_live_mapping.py'\nassert (root/'run_oracle_LIVE.pre_ksem077.py').is_file()\nr=json.loads((root/'qseries_v2/kalshi_sports_evidence_mapping/state/ksem077_native_launcher_cutover.json').read_text())\nassert r['execution_authority'] is False\nprint('[PASS] KSEM child inserted into exact native production CHILDREN dict with rollback backup')\nprint('[PASS] KSEM-077 certified')\n""",encoding="utf-8")
    print("[PASS] native child inserted:",KEY,"=>",RUNNER)
    print("[PASS] AST parse and exact dict readback verified")
    print("[PASS] KSEM-077 installer complete")
if __name__=="__main__": main()
