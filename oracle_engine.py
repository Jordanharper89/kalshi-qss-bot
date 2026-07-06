"""
Oracle Engine

ORACLE-022.9

Purpose:
- Single high-level interface for Oracle.
- This is the ONLY class the Telegram bot should use.
"""

from typing import Any, Dict, List

from oracle_command_router import OracleCommandRouter


class OracleEngine:
    def __init__(self, kernel):
        self.kernel = kernel
        self.router = OracleCommandRouter(kernel)

    def start(self):
        return self.router.execute("start")

    def stop(self):
        return self.router.execute("stop")

    def run(self):
        return self.router.execute("run")

    def feed(self):
        return self.router.execute("feed")

    def status(self):
        return self.router.execute("status")

    def metrics(self):
        return self.router.execute("metrics")

    def save(self):
        return self.router.execute("save")

    def restore(self):
        return self.router.execute("restore")

    def execute(self, command: str) -> Dict[str, Any]:
        return self.router.execute(command)

    def available_commands(self) -> List[str]:
        return [
            "start",
            "stop",
            "run",
            "feed",
            "status",
            "metrics",
            "save",
            "restore",
        ]


oracle_engine = None


def initialize_oracle_engine(kernel):
    global oracle_engine

    oracle_engine = OracleEngine(kernel)

    return oracle_engine