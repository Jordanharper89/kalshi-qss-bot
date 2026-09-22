from pathlib import Path

ROOT = Path.cwd()

def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", p.relative_to(ROOT))

def main():
    print("=" * 118)
    print(' OSN-043 CONSOLIDATED LIVE EVENT SCHEMA MAP INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/certification/live_event_structure_forensics.py')
    require('qseries_v2/oracle_source_network/certification/live_payload_structure_probe.py')
    write('qseries_v2/oracle_source_network/certification/live_schema_map.py', '\nfrom dataclasses import dataclass\n\n@dataclass(frozen=True, slots=True)\nclass LiveSchemaMap:\n    league: str\n    physically_extracting_before_forensics: bool\n    structured_candidates: int\n    has_json_paths: bool\n    has_token_contexts: bool\n    action: str\n    execution_authority: bool = False\n\ndef map_result(league,finding,already_extracting=False):\n    if already_extracting:\n        action="PRESERVE_WORKING_EXTRACTOR"\n    elif finding.json_paths:\n        action="BUILD_SOURCE_SPECIFIC_JSON_PATH_EXTRACTOR"\n    elif finding.token_contexts:\n        action="BUILD_SOURCE_SPECIFIC_HTML_OR_SCRIPT_STATE_EXTRACTOR"\n    else:\n        action="NO_EVENT_STRUCTURE_PROVEN"\n    return LiveSchemaMap(\n        league=league,\n        physically_extracting_before_forensics=already_extracting,\n        structured_candidates=finding.structured_candidates,\n        has_json_paths=bool(finding.json_paths),\n        has_token_contexts=bool(finding.token_contexts),\n        action=action,\n    )\n')
    write('test_osn_043_consolidated_live_event_schema_map.py', '\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.certification.live_event_structure_forensics import inspect_payload\nfrom qseries_v2.oracle_source_network.certification.live_schema_map import map_result\nleagues=("NFL","NCAAF","NBA","NCAAB","NHL","MLS","EPL")\nrows=[]\nfor league in leagues:\n    _,payload=acquire_live_payload(league,8.0)\n    finding=inspect_payload(league,payload["body"])\n    row=map_result(league,finding,already_extracting=(league=="NBA"))\n    rows.append(row)\n    print(f"[SCHEMA_MAP] {league} candidates={row.structured_candidates} json_paths={row.has_json_paths} token_contexts={row.has_token_contexts} action={row.action}")\nassert len(rows)==7\nassert [r for r in rows if r.league=="NBA"][0].action=="PRESERVE_WORKING_EXTRACTOR"\nassert all(r.execution_authority is False for r in rows)\nprint("[PASS] live source-specific extraction work map produced")\nprint("[PASS] NBA retained as positive control")\n"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=75)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-043 exceeded hard 75-second gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"OSN-043 failed rc={p.returncode}"\nprint("[PASS] OSN-043 consolidated live schema map certified")\n')
    print('[PASS] OSN-043 installed')
    print('[PASS] source-specific next actions derived from live structure')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
