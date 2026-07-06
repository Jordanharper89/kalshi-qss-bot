from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_master_control.py")


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle079_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-079 INSTALLER")
    print(" Master Control Data Quality Link")
    print("===================================")

    if not TARGET.exists():
        raise FileNotFoundError("oracle_master_control.py not found")

    text = TARGET.read_text(encoding="utf-8", errors="ignore")
    b = backup(TARGET)

    if '"data": ["python", "oracle_data_quality_terminal.py"]' not in text:
        text = text.replace(
            '"state_status": ["python", "oracle_state_maintenance.py", "status"],',
            '"state_status": ["python", "oracle_state_maintenance.py", "status"],\n'
            '    "data": ["python", "oracle_data_quality_terminal.py"],\n'
            '    "data_full": ["python", "oracle_data_quality_terminal.py", "full"],',
        )

    if 'python oracle_master_control.py data' not in text:
        text = text.replace(
            'print(" python oracle_master_control.py backup")',
            'print(" python oracle_master_control.py backup")\n'
            '    print(" python oracle_master_control.py data")\n'
            '    print(" python oracle_master_control.py data full")',
        )

    if 'if key in COMMANDS:' in text and 'if key == "data":' not in text:
        text = text.replace(
            '    key = args[0]\n\n    if key in COMMANDS:',
            '    key = args[0]\n\n'
            '    if key == "data":\n'
            '        if len(args) > 1 and args[1] == "full":\n'
            '            run_cmd(COMMANDS["data_full"])\n'
            '        else:\n'
            '            run_cmd(COMMANDS["data"])\n'
            '        return\n\n'
            '    if key in COMMANDS:',
        )

    TARGET.write_text(text, encoding="utf-8")

    print("[OK] Patched oracle_master_control.py")
    print(f"[OK] Backup created: {b}")
    print("")
    print("Tests:")
    print(" python oracle_master_control.py menu")
    print(" python oracle_master_control.py data")
    print(" python oracle_master_control.py data full")
    print("")
    print("[DONE] ORACLE-079 Master Control Data Quality Link installed")


if __name__ == "__main__":
    main()