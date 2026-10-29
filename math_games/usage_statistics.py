"""Small, failure-isolated SQLite store for anonymous game usage statistics."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class UsageStatistics:
    """Persist and aggregate anonymous game-session events.

    This class deliberately contains no Flask dependencies, making it safe to
    call from request handling and straightforward to test.  Callers should
    treat it as best-effort: statistics must never affect gameplay.
    """

    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _timestamp(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat(timespec="seconds")

    def _connect(self) -> sqlite3.Connection:
        # Do not make a player wait on a locked analytics database.  Callers
        # catch the resulting operational error and continue the game.
        connection = sqlite3.connect(self.database_path, timeout=0.05)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS game_sessions (
                    session_id TEXT PRIMARY KEY,
                    game_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    questions_answered INTEGER NOT NULL DEFAULT 0,
                    duration_seconds REAL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS answered_questions (
                    session_id TEXT NOT NULL,
                    question_number INTEGER NOT NULL,
                    PRIMARY KEY (session_id, question_number),
                    FOREIGN KEY (session_id) REFERENCES game_sessions(session_id)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_game_sessions_started_at "
                "ON game_sessions(started_at)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_game_sessions_game_id "
                "ON game_sessions(game_id)"
            )

    def start_session(self, session_id: str, game_id: str) -> None:
        """Record a session once.  Replayed start requests do not double count."""
        with self._connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO game_sessions (session_id, game_id, started_at)
                VALUES (?, ?, ?)
                """,
                (session_id, game_id, self._timestamp(self._now())),
            )

    def record_question(self, session_id: str, question_number: int) -> None:
        """Record one resolved question once for a session."""
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO answered_questions (session_id, question_number)
                VALUES (?, ?)
                """,
                (session_id, question_number),
            )
            if cursor.rowcount:
                connection.execute(
                    """
                    UPDATE game_sessions
                    SET questions_answered = questions_answered + 1
                    WHERE session_id = ?
                    """,
                    (session_id,),
                )

    def complete_session(self, session_id: str) -> None:
        """Mark a session complete once and retain its elapsed duration."""
        finished_at = self._now()
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT started_at FROM game_sessions
                WHERE session_id = ? AND completed_at IS NULL
                """,
                (session_id,),
            ).fetchone()
            if row is None:
                return
            started_at = datetime.fromisoformat(row["started_at"])
            seconds = max(0.0, (finished_at - started_at).total_seconds())
            connection.execute(
                """
                UPDATE game_sessions
                SET completed_at = ?, duration_seconds = ?
                WHERE session_id = ? AND completed_at IS NULL
                """,
                (self._timestamp(finished_at), seconds, session_id),
            )

    def dashboard(self, days: Optional[int] = 30) -> Dict[str, Any]:
        """Return the read-only dashboard model for the requested date range."""
        now = self._now()
        today = now.date()
        start_date = today - timedelta(days=days - 1) if days else None
        start_timestamp = (
            self._timestamp(datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc))
            if start_date
            else None
        )

        with self._connection() as connection:
            lifetime = connection.execute(
                """
                SELECT COUNT(*) AS started,
                       SUM(completed_at IS NOT NULL) AS completed,
                       COALESCE(SUM(questions_answered), 0) AS questions,
                       COALESCE(SUM(duration_seconds), 0) AS duration_seconds,
                       AVG(duration_seconds) AS average_duration,
                       MIN(started_at) AS first_activity,
                       MAX(COALESCE(completed_at, started_at)) AS most_recent
                FROM game_sessions
                """
            ).fetchone()

            where = ""
            parameters: tuple[Any, ...] = ()
            if start_timestamp:
                where = "WHERE started_at >= ?"
                parameters = (start_timestamp,)

            selected = connection.execute(
                f"""
                SELECT COUNT(*) AS started,
                       SUM(completed_at IS NOT NULL) AS completed
                FROM game_sessions {where}
                """,
                parameters,
            ).fetchone()
            by_game = connection.execute(
                f"""
                SELECT game_id, COUNT(*) AS started,
                       SUM(completed_at IS NOT NULL) AS completed
                FROM game_sessions {where}
                GROUP BY game_id
                ORDER BY started DESC, game_id ASC
                """,
                parameters,
            ).fetchall()
            daily_rows = connection.execute(
                f"""
                SELECT substr(started_at, 1, 10) AS day, COUNT(*) AS count
                FROM game_sessions {where}
                GROUP BY day ORDER BY day ASC
                """,
                parameters,
            ).fetchall()
            weekly = connection.execute(
                f"""
                SELECT strftime('%Y-W%W', started_at) AS period, COUNT(*) AS count
                FROM game_sessions {where}
                GROUP BY period ORDER BY period DESC LIMIT 8
                """,
                parameters,
            ).fetchall()
            monthly = connection.execute(
                f"""
                SELECT substr(started_at, 1, 7) AS period, COUNT(*) AS count
                FROM game_sessions {where}
                GROUP BY period ORDER BY period DESC LIMIT 12
                """,
                parameters,
            ).fetchall()
            recent = connection.execute(
                f"""
                SELECT game_id, started_at, completed_at, questions_answered, duration_seconds
                FROM game_sessions {where}
                ORDER BY started_at DESC LIMIT 20
                """,
                parameters,
            ).fetchall()

        daily_counts = {row["day"]: row["count"] for row in daily_rows}
        if start_date is None:
            first_activity = lifetime["first_activity"]
            chart_start = date.fromisoformat(first_activity[:10]) if first_activity else today
        else:
            chart_start = start_date
        # A daily graph is useful without becoming an unreadable wall of dates.
        chart_start = max(chart_start, today - timedelta(days=364)) if days is None else chart_start
        activity: List[Dict[str, Any]] = []
        cursor = chart_start
        while cursor <= today:
            key = cursor.isoformat()
            activity.append({"date": key, "label": f"{cursor.strftime('%b')} {cursor.day}", "count": daily_counts.get(key, 0)})
            cursor += timedelta(days=1)

        first_activity = lifetime["first_activity"]
        if first_activity:
            active_days = max(1, (today - date.fromisoformat(first_activity[:10])).days + 1)
        else:
            active_days = 1
        started = int(lifetime["started"] or 0)
        averages = {
            "per_day": started / active_days,
            "per_week": started / max(1, active_days / 7),
        }
        return {
            "lifetime": dict(lifetime),
            "selected": dict(selected),
            "activity": activity,
            "by_game": [dict(row) for row in by_game],
            "weekly": [dict(row) for row in reversed(weekly)],
            "monthly": [dict(row) for row in reversed(monthly)],
            "recent": [dict(row) for row in recent],
            "averages": averages,
        }
