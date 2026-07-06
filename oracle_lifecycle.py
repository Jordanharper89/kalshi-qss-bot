"""
Oracle Lifecycle Manager

ORACLE-022.5

Purpose:
- Control Oracle startup/shutdown.
- Manage Oracle runtime state.
- Publish lifecycle events.
"""

from enum import Enum

from oracle_event_bus import oracle_event_bus, OracleEvents
from oracle_logger import oracle_logger


class OracleState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    ERROR = "ERROR"


class OracleLifecycle:
    def __init__(self):
        self._state = OracleState.STOPPED

    @property
    def state(self):
        return self._state

    def start(self):
        if self._state == OracleState.RUNNING:
            return False

        self._set_state(OracleState.STARTING)

        oracle_logger.info("Oracle starting...")

        self._set_state(OracleState.RUNNING)

        oracle_logger.info("Oracle running.")

        return True

    def stop(self):
        if self._state == OracleState.STOPPED:
            return False

        self._set_state(OracleState.STOPPING)

        oracle_logger.info("Oracle stopping...")

        self._set_state(OracleState.STOPPED)

        oracle_logger.info("Oracle stopped.")

        return True

    def error(self, message: str):
        self._set_state(OracleState.ERROR)

        oracle_logger.error(message)

        oracle_event_bus.publish(
            OracleEvents.ERROR,
            message,
        )

    def snapshot(self):
        return {
            "state": self._state.value,
        }

    def _set_state(self, state: OracleState):
        self._state = state

        oracle_event_bus.publish(
            OracleEvents.STATUS_CHANGED,
            {
                "state": state.value,
            },
        )


oracle_lifecycle = OracleLifecycle()