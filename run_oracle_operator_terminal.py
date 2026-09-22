from __future__ import annotations

import run_oracle_open_intelligence_terminal as base

from qseries_v2.oracle_terminal.oracle_historical_experience_terminal_binding import (
    bind_historical_experience_surface,
)

from qseries_v2.oracle_terminal.oracle_persisted_trader_intelligence_terminal_binding import (
    bind_persisted_trader_intelligence,
)

from qseries_v2.oracle_intelligence_analytics_runtime.oiar_026_operator_terminal_trader_brief_cutover import (
    bind_trader_brief_terminal,
)

from qseries_v2.oracle_intelligence_analytics_runtime.oiar_055_proven_current_operator_terminal_cutover import (
    bind_current_trader_terminal,
)


def main():
    bind_historical_experience_surface(base)
    bind_persisted_trader_intelligence(base)
    bind_trader_brief_terminal(base)
    bind_current_trader_terminal(base)

    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
