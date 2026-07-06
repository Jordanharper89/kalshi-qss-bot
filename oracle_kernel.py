"""
Oracle Kernel

ORACLE-022.7

Purpose:
- Central entry point for all Oracle operations.
- Owns the Oracle Runtime.
- Exposes a simple API for the Telegram bot.
"""

from typing import Any, Dict, List

from oracle_runtime import OracleRuntime


class OracleKernel:
    def __init__(self, runtime: OracleRuntime):
        self.runtime = runtime

    def start(self) -> None:
        self.runtime.start()

    def stop(self) -> None:
        self.runtime.stop()

    def research_cycle(self) -> Dict[str, Any]:
        return self.runtime.run_cycle()

    def opportunity_feed(self) -> List[Dict[str, Any]]:
        return self.runtime.opportunity_feed()

    def status(self) -> Dict[str, Any]:
        return self.runtime.status()

    def metrics(self) -> Dict[str, Any]:
        return self.runtime.metrics_snapshot()

    def save(self) -> None:
        self.runtime.save_state()

    def restore(self) -> Dict[str, Any]:
        return self.runtime.load_state()


oracle_kernel = None


def initialize_oracle_kernel(runtime: OracleRuntime) -> OracleKernel:
    global oracle_kernel

    oracle_kernel = OracleKernel(runtime)

    return oracle_kernel