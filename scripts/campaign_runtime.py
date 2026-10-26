"""Durable, content-free campaign accounting and a machine-wide lease."""

from __future__ import annotations

import json
import os
import socket
import sqlite3
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Self


class CampaignBlocked(RuntimeError):
    """Raised when a reservation or attempt would violate a campaign limit."""


class CampaignLease(AbstractContextManager["CampaignLease"]):
    """Nonblocking OS lock shared by every local project launcher."""

    def __init__(self, path: Path, campaign_id: str) -> None:
        self.path = path
        self.campaign_id = campaign_id
        self._handle = None

    def acquire(self) -> CampaignLease:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            handle.close()
            raise CampaignBlocked("another lab campaign holds the execution lease") from exc
        self._handle = handle
        metadata = {
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "campaign_id": self.campaign_id,
            "acquired_at_utc": datetime.now(UTC).isoformat(),
        }
        try:
            handle.seek(0)
            handle.truncate()
            handle.write(json.dumps(metadata, sort_keys=True).encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        except OSError:
            self.release()
            raise
        return self

    def release(self) -> None:
        if self._handle is None:
            return
        handle, self._handle = self._handle, None
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()

    def __enter__(self) -> Self:
        return self.acquire()

    def __exit__(self, *_: object) -> None:
        self.release()


class CampaignLedger:
    """Append-only SQLite journal; reserved attempts survive process crashes."""

    def __init__(
        self, path: Path, *, project: str, campaign_id: str, read_only: bool = False
    ) -> None:
        self.path = path
        self.project = project
        self.campaign_id = campaign_id
        self.read_only = read_only
        if not read_only:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        db = self._open_connection()
        try:
            if read_only:
                exists = db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='events'"
                ).fetchone()
                if exists is None:
                    raise CampaignBlocked("campaign ledger schema is invalid")
            else:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("PRAGMA synchronous=FULL")
                db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS events (
                        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                        project TEXT NOT NULL,
                        campaign_id TEXT NOT NULL,
                        case_id TEXT NOT NULL,
                        trial INTEGER NOT NULL,
                        event TEXT NOT NULL CHECK(event IN ('reserved','completed')),
                        reserved_calls INTEGER NOT NULL,
                        reserved_input_tokens INTEGER NOT NULL,
                        reserved_output_tokens INTEGER NOT NULL,
                        reserved_cost_usd TEXT NOT NULL,
                        actual_input_tokens INTEGER,
                        actual_output_tokens INTEGER,
                        actual_cost_usd TEXT,
                        outcome TEXT,
                        error_class TEXT,
                        created_at_utc TEXT NOT NULL,
                        UNIQUE(project, campaign_id, case_id, trial, event)
                    );
                    CREATE TRIGGER IF NOT EXISTS events_no_update
                    BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'ledger is append-only'); END;
                    CREATE TRIGGER IF NOT EXISTS events_no_delete
                    BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'ledger is append-only'); END;
                    """
                )
        finally:
            db.close()

    def _open_connection(self) -> sqlite3.Connection:
        if self.read_only:
            uri = f"file:{self.path.as_posix()}?mode=ro"
            return sqlite3.connect(uri, uri=True, timeout=30)
        return sqlite3.connect(self.path, timeout=30, isolation_level="IMMEDIATE")

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = self._open_connection()
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def _latest(self, db: sqlite3.Connection) -> list[sqlite3.Row]:
        db.row_factory = sqlite3.Row
        return db.execute(
            """
            SELECT e.* FROM events e
            JOIN (SELECT project,campaign_id,case_id,trial,MAX(sequence) sequence
                  FROM events GROUP BY project,campaign_id,case_id,trial) latest
            ON e.sequence=latest.sequence
            """
        ).fetchall()

    def totals(self) -> dict[str, Decimal | int]:
        with self._connect() as db:
            rows = self._latest(db)
        requests = sum(row["reserved_calls"] for row in rows)
        input_tokens = sum(
            row["actual_input_tokens"]
            if row["actual_input_tokens"] is not None
            else row["reserved_input_tokens"]
            for row in rows
        )
        output_tokens = sum(
            row["actual_output_tokens"]
            if row["actual_output_tokens"] is not None
            else row["reserved_output_tokens"]
            for row in rows
        )
        cost = sum(
            (
                Decimal(row["actual_cost_usd"])
                if row["actual_cost_usd"] is not None
                else Decimal(row["reserved_cost_usd"])
            )
            for row in rows
        )
        return {
            "requests": requests,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": cost,
        }

    def reserve(
        self,
        *,
        case_id: str,
        trial: int,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: Decimal,
        caps: dict[str, int | Decimal],
    ) -> None:
        if trial < 1 or input_tokens < 1 or output_tokens < 1 or estimated_cost_usd < 0:
            raise CampaignBlocked("invalid trial reservation")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = self._latest(db)
            existing = next(
                (
                    row
                    for row in rows
                    if row["project"] == self.project
                    and row["campaign_id"] == self.campaign_id
                    and row["case_id"] == case_id
                    and row["trial"] == trial
                ),
                None,
            )
            if existing is not None:
                raise CampaignBlocked(
                    "trial already has a reservation or result; it will not be rerun"
                )
            totals = self.totals()
            projected = {
                "requests": totals["requests"] + 1,
                "input_tokens": totals["input_tokens"] + input_tokens,
                "output_tokens": totals["output_tokens"] + output_tokens,
                "estimated_cost_usd": totals["estimated_cost_usd"] + estimated_cost_usd,
            }
            if any(projected[key] > caps[key] for key in projected):
                raise CampaignBlocked("campaign cumulative reservation cap would be exceeded")
            db.execute(
                "INSERT INTO events(project,campaign_id,case_id,trial,event,reserved_calls,"
                "reserved_input_tokens,reserved_output_tokens,reserved_cost_usd,created_at_utc) "
                "VALUES(?,?,?,?, 'reserved',1,?,?,?,?)",
                (
                    self.project,
                    self.campaign_id,
                    case_id,
                    trial,
                    input_tokens,
                    output_tokens,
                    str(estimated_cost_usd),
                    datetime.now(UTC).isoformat(),
                ),
            )

    def complete(
        self,
        *,
        case_id: str,
        trial: int,
        actual_input_tokens: int | None,
        actual_output_tokens: int | None,
        actual_cost_usd: Decimal | None,
        outcome: str,
        error_class: str | None = None,
    ) -> None:
        if outcome not in {"passed", "failed", "provider_error"}:
            raise CampaignBlocked("invalid sanitized trial outcome")
        if any(
            value is not None and value < 0
            for value in (actual_input_tokens, actual_output_tokens, actual_cost_usd)
        ):
            raise CampaignBlocked("observed usage cannot be negative")
        with self._connect() as db:
            reserved = db.execute(
                "SELECT 1 FROM events WHERE project=? AND campaign_id=? AND case_id=? "
                "AND trial=? AND event='reserved'",
                (self.project, self.campaign_id, case_id, trial),
            ).fetchone()
            if reserved is None:
                raise CampaignBlocked("cannot complete an unreserved trial")
            db.execute(
                "INSERT INTO events(project,campaign_id,case_id,trial,event,reserved_calls,"
                "reserved_input_tokens,reserved_output_tokens,reserved_cost_usd,actual_input_tokens,"
                "actual_output_tokens,actual_cost_usd,outcome,error_class,created_at_utc) "
                "SELECT project,campaign_id,case_id,trial,'completed',reserved_calls,"
                "reserved_input_tokens,reserved_output_tokens,reserved_cost_usd,?,?,?,?,?,? "
                "FROM events WHERE project=? AND campaign_id=? AND case_id=? AND trial=? "
                "AND event='reserved'",
                (
                    actual_input_tokens,
                    actual_output_tokens,
                    str(actual_cost_usd) if actual_cost_usd is not None else None,
                    outcome,
                    error_class,
                    datetime.now(UTC).isoformat(),
                    self.project,
                    self.campaign_id,
                    case_id,
                    trial,
                ),
            )

    def export_jsonl(self, path: Path) -> None:
        with self._connect() as db:
            rows = db.execute(
                "SELECT project,campaign_id,case_id,trial,event,reserved_calls,"
                "reserved_input_tokens,reserved_output_tokens,reserved_cost_usd,"
                "actual_input_tokens,actual_output_tokens,actual_cost_usd,outcome,error_class,"
                "created_at_utc FROM events WHERE project=? AND campaign_id=? ORDER BY sequence",
                (self.project, self.campaign_id),
            ).fetchall()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for row in rows:
                stream.write(json.dumps(dict(row), sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)

    def reserved_trials(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT case_id,trial,event,outcome,error_class FROM events "
                "WHERE project=? AND campaign_id=? ORDER BY sequence",
                (self.project, self.campaign_id),
            ).fetchall()
        latest: dict[tuple[str, int], dict[str, Any]] = {}
        for case_id, trial, event, outcome, error_class in rows:
            latest[(case_id, trial)] = {
                "case_id": case_id,
                "trial": trial,
                "event": event,
                "outcome": outcome,
                "error_class": error_class,
            }
        return list(latest.values())
