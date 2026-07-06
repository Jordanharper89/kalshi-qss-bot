"""
Oracle Command Router

ORACLE-022.8

Purpose:
- Single routing layer between Telegram and Oracle.
- All Oracle commands pass through here.
"""

from typing import Any, Dict


class OracleCommandRouter:
    def __init__(self, kernel: Any):
        self.kernel = kernel

    def execute(self, command: str) -> Dict[str, Any]:
        command = (command or "").strip().lower()

        routes = {
            "run": self.kernel.research_cycle,
            "feed": self.kernel.opportunity_feed,
            "status": self.kernel.status,
            "metrics": self.kernel.metrics,
            "save": self.kernel.save,
            "restore": self.kernel.restore,
            "start": self.kernel.start,
            "stop": self.kernel.stop,
        }

        handler = routes.get(command)

        if handler is None:
            return {
                "success": False,
                "command": command,
                "error": "Unknown Oracle command.",
            }

        try:
            result = handler()

            return {
                "success": True,
                "command": command,
                "result": result,
            }

        except Exception as error:
            return {
                "success": False,
                "command": command,
                "error": str(error),
            }


oracle_router = None


def initialize_oracle_router(kernel):
    global oracle_router

    oracle_router = OracleCommandRouter(kernel)

    return oracle_router