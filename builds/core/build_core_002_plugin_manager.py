"""
build_core_002_plugin_manager.py
"""

from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2"
CORE = PKG / "core"
PLUGINS = ROOT / "plugins"

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"[OK] Wrote {path.relative_to(ROOT)}")

def main():
    print("="*35)
    print(" CORE-002 INSTALLER")
    print(" Plugin Manager")
    print("="*35)

    write(CORE/"plugin_contract.py", '"""Plugin contract."""\n\nclass Plugin:\n    pass\n')
    write(CORE/"plugin_manager.py", '"""Plugin manager."""\n\nclass PluginManager:\n    def __init__(self):\n        self.plugins = {}\n')
    write(CORE/"plugin_loader.py", '"""Plugin loader."""\n\nclass PluginLoader:\n    pass\n')
    write(PLUGINS/"__init__.py", "")
    write(PLUGINS/"README.md", "# Plugins\\n")

    write(ROOT/"test_core_002_plugin_manager.py",
          "from qseries_v2.core.plugin_manager import PluginManager\\n"
          "PluginManager()\\n"
          "print('[PASS] CORE-002 smoke test')\\n")

    print("\n[DONE] CORE-002 installed")
    print("Run:")
    print(" python test_core_002_plugin_manager.py")

if __name__ == "__main__":
    main()