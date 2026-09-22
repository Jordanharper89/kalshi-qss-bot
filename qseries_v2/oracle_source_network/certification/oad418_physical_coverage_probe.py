
from pathlib import Path
from qseries_v2.oracle_source_network.coverage.oad418_probe import module_public_data, report_files

def extract_candidate_records(root: Path):
    rows = []
    for item in report_files(root):
        val = item["value"]
        if isinstance(val, list):
            rows.extend(val)
        elif isinstance(val, dict):
            for key in ("markets","rows","gaps","priorities","results","items"):
                v = val.get(key)
                if isinstance(v, list):
                    rows.extend(v)
    if rows:
        return rows, "oad418_report_files"

    public = module_public_data(root)
    for item in public:
        val = item["value"]
        if isinstance(val, (list, tuple)):
            rows.extend(list(val))
    return rows, "oad418_module_public_data"
