from pathlib import Path
import json,hashlib
def certify(root=None):
    base=Path(root or Path.cwd()).resolve()
    s86=json.loads((base/'qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json').read_text())
    s88=json.loads((base/'qseries_v2/oracle_source_network/state/osn088_extension_supervisor.json').read_text())
    s89=json.loads((base/'qseries_v2/oracle_source_network/state/osn089_bounded_dual_runtime_physical_gate.json').read_text())
    unchanged=hashlib.sha256((base/s86['launcher_path']).read_bytes()).hexdigest()==s86['launcher_sha256']
    ready=bool(unchanged and (base/s88['launcher']).exists() and s89.get('base_launcher_boot_alive') and s89.get('sports_cycle_completed'))
    return {'admitted':['NFL','NCAAF','NBA','NHL','MLS','EPL'],'held':['NCAAB','MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED'],'blocked':['UCL'],'base_launcher_unchanged':unchanged,'production_extension_launcher':s88['launcher'],'bounded_dual_runtime_certified':bool(s89.get('base_launcher_boot_alive') and s89.get('sports_cycle_completed')),'activation_ready':ready,'terminal_dependency':'NONE','execution_authority':False}
