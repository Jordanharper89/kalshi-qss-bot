"""
OI-073 Runtime Safety Guard

Purpose:
- Enforce Oracle read-only runtime boundary.
- Validate runtime commands, payloads, and outputs.
- Block anything that looks like trade execution, order placement, mutation, or cancellation.
- Preserve separation: Oracle = research, Q Series = execution.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List


FORBIDDEN_TERMS = {
    "place_order",
    "submit_order",
    "execute_trade",
    "buy",
    "sell",
    "cancel_order",
    "modify_order",
    "fill_order",
    "market_order",
    "limit_order",
    "position_size",
    "order_id",
    "execution_enabled:true",
}


ALLOWED_COMMANDS = {
    "status",
    "dashboard",
    "health_report",
    "run_once",
    "start_runtime",
    "stop_runtime",
    "startup_check",
    "recover_and_start",
    "persist_status",
    "persist_dashboard",
    "persist_full_state",
    "restore_summary",
    "research_report",
    "consensus_report",
    "refresh_due_sessions",
    "portfolio_snapshot",
}


class RuntimeSafetyGuard:
    module_name = "oi_073_runtime_safety_guard"

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "allowed_commands": sorted(ALLOWED_COMMANDS),
            "forbidden_terms": sorted(FORBIDDEN_TERMS),
        }

    def validate_command(self, command: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        payload = payload or {}
        command = str(command or "").strip()

        violations = []

        if command not in ALLOWED_COMMANDS:
            violations.append({
                "type": "unknown_or_disallowed_command",
                "value": command,
            })

        text = self._flatten_text({
            "command": command,
            "payload": payload,
        })

        violations.extend(self._find_forbidden_terms(text))

        allowed = len(violations) == 0

        return {
            "module": self.module_name,
            "status": "ok" if allowed else "blocked",
            "read_only": True,
            "allowed": allowed,
            "command": command,
            "violations": violations,
            "decision": "allow" if allowed else "block",
        }

    def validate_runtime_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        text = self._flatten_text(output)
        violations = self._find_forbidden_terms(text)

        execution_flags = self._find_execution_flags(output)
        violations.extend(execution_flags)

        allowed = len(violations) == 0

        return {
            "module": self.module_name,
            "status": "ok" if allowed else "blocked",
            "read_only": True,
            "allowed": allowed,
            "violations": violations,
            "decision": "allow" if allowed else "block",
        }

    def guarded_command_result(
        self,
        command: str,
        payload: Dict[str, Any] | None,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        command_check = self.validate_command(command, payload)
        output_check = self.validate_runtime_output(result)

        allowed = command_check["allowed"] and output_check["allowed"]

        return {
            "module": self.module_name,
            "status": "ok" if allowed else "blocked",
            "read_only": True,
            "allowed": allowed,
            "command_check": command_check,
            "output_check": output_check,
            "result": result if allowed else None,
            "blocked_result": None if allowed else result,
        }

    def _find_forbidden_terms(self, text: str) -> List[Dict[str, Any]]:
        text = text.lower()
        violations = []

        for term in FORBIDDEN_TERMS:
            if term.lower() in text:
                violations.append({
                    "type": "forbidden_term",
                    "value": term,
                })

        return violations

    def _find_execution_flags(self, obj: Any, path: str = "") -> List[Dict[str, Any]]:
        violations = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                next_path = f"{path}.{key}" if path else str(key)

                if str(key).lower() == "execution_enabled" and value is True:
                    violations.append({
                        "type": "execution_enabled_true",
                        "path": next_path,
                        "value": value,
                    })

                if str(key).lower() == "actionable" and value is True:
                    violations.append({
                        "type": "actionable_true",
                        "path": next_path,
                        "value": value,
                    })

                violations.extend(self._find_execution_flags(value, next_path))

        elif isinstance(obj, list):
            for idx, value in enumerate(obj):
                violations.extend(self._find_execution_flags(value, f"{path}[{idx}]"))

        return violations

    def _flatten_text(self, obj: Any) -> str:
        if isinstance(obj, dict):
            return " ".join(f"{k} {self._flatten_text(v)}" for k, v in obj.items())

        if isinstance(obj, list):
            return " ".join(self._flatten_text(v) for v in obj)

        return str(obj)


runtime_safety_guard = RuntimeSafetyGuard()
