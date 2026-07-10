from qseries_v2.ops.runtime_path_audit_runner import run_runtime_path_audit_runner

result = run_runtime_path_audit_runner()

print("========================================")
print(" OPS-010 REAL REPO AUDIT")
print("========================================")
print(f"Status: {result['status']}")
print(f"Findings: {result['finding_count']}")
print(f"JSON Report: {result['json_report']}")
print(f"Text Report: {result['text_report']}")

if result["findings"]:
    print("")
    print("Findings:")
    for finding in result["findings"]:
        print(f"- {finding['file']}:{finding['line']} | {finding['pattern']} | {finding['text']}")