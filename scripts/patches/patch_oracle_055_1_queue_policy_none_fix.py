from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_execution_queue_manager.py")


def backup(path):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle055_1_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-055.1 INSTALLER")
    print(" Queue Policy None Fix")
    print("===================================")

    if not TARGET.exists():
        raise FileNotFoundError("oracle_execution_queue_manager.py not found")

    text = TARGET.read_text(encoding="utf-8", errors="ignore")
    b = backup(TARGET)

    old = '''        policy = item.get("execution_gate", {}).get("execution_policy") if isinstance(item.get("execution_gate"), dict) else {}
        policy_data = policy.get("policy") if isinstance(policy, dict) else {}
'''

    new = '''        policy = item.get("execution_gate", {}).get("execution_policy") if isinstance(item.get("execution_gate"), dict) else {}
        if not isinstance(policy, dict):
            policy = {}
        policy_data = policy.get("policy")
        if not isinstance(policy_data, dict):
            policy_data = {}
'''

    if old not in text:
        print("[WARN] Exact block not found. Applying fallback patch.")
        text = text.replace(
            '''        policy_data = policy.get("policy") if isinstance(policy, dict) else {}
''',
            '''        policy_data = policy.get("policy") if isinstance(policy, dict) else {}
        if not isinstance(policy_data, dict):
            policy_data = {}
''',
        )
    else:
        text = text.replace(old, new, 1)

    TARGET.write_text(text, encoding="utf-8")

    print("[OK] Patched oracle_execution_queue_manager.py")
    print(f"[OK] Backup created: {b}")
    print("")
    print("Tests:")
    print(" python oracle_execution_queue_manager.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('execution_queue_status')); print(s.get('execution_queue')[:3])\"")
    print("")
    print("[DONE] ORACLE-055.1 Queue Policy None Fix installed")


if __name__ == "__main__":
    main()