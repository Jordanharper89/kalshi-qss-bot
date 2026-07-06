"""
Oracle Run Manager

ORACLE-008

Purpose:
- Give every Oracle pipeline run a unique run ID.
- Track pipeline step timing.
- Store run status.
"""

import time
import uuid
from contextlib import contextmanager
from datetime import datetime

from oracle.database.db import get_connection, init_db


def now_utc() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


class OracleRunManager:
    def __init__(self):
        init_db()
        self.run_id = f"ORA-RUN-{uuid.uuid4().hex[:10].upper()}"
        self.started = time.time()

    def start_run(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO oracle_runs (
                run_id,
                started_at,
                status,
                notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                self.run_id,
                now_utc(),
                "running",
                "Oracle Phase 1 pipeline run",
            ),
        )

        conn.commit()
        conn.close()

        print(f"Oracle Run ID: {self.run_id}")

    def finish_run(self, status: str = "success", notes: str = ""):
        duration = round(time.time() - self.started, 3)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE oracle_runs
            SET finished_at = ?,
                duration_seconds = ?,
                status = ?,
                notes = ?
            WHERE run_id = ?
            """,
            (
                now_utc(),
                duration,
                status,
                notes,
                self.run_id,
            ),
        )

        conn.commit()
        conn.close()

        print(f"Oracle run finished: {status}")
        print(f"Duration: {duration} seconds")

    @contextmanager
    def step(self, step_name: str):
        step_started = time.time()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO pipeline_steps (
                run_id,
                step_name,
                started_at,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                self.run_id,
                step_name,
                now_utc(),
                "running",
            ),
        )

        step_id = cursor.lastrowid

        conn.commit()
        conn.close()

        print("")
        print(f"--- Starting step: {step_name} ---")

        try:
            result = {"records_processed": 0}
            yield result

            duration = round(time.time() - step_started, 3)

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE pipeline_steps
                SET finished_at = ?,
                    duration_seconds = ?,
                    status = ?,
                    records_processed = ?
                WHERE id = ?
                """,
                (
                    now_utc(),
                    duration,
                    "success",
                    result.get("records_processed", 0),
                    step_id,
                ),
            )

            conn.commit()
            conn.close()

            print(f"--- Finished step: {step_name} | {duration}s ---")

        except Exception as e:
            duration = round(time.time() - step_started, 3)

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE pipeline_steps
                SET finished_at = ?,
                    duration_seconds = ?,
                    status = ?,
                    error_message = ?
                WHERE id = ?
                """,
                (
                    now_utc(),
                    duration,
                    "failed",
                    str(e),
                    step_id,
                ),
            )

            conn.commit()
            conn.close()

            print(f"--- Failed step: {step_name} | {duration}s ---")
            raise