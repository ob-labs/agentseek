"""Persistent chat session store for the Marimo dashboard."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, MetaData, Table, Text, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import sessionmaker as sessionmaker_type
from sqlalchemy.schema import Column
from sqlalchemy.sql.sqltypes import String

import bubseek.oceanbase  # noqa: F401 - register mysql+oceanbase dialect


class TurnConflictError(RuntimeError):
    """Raised when a session already has a running turn."""


@dataclass(frozen=True, slots=True)
class SessionSnapshot:
    session_id: str
    status: str
    active_turn_id: str | None
    last_event_id: int
    updated_at: str
    last_error: str | None

    def as_dict(self) -> dict[str, str | int | None]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ChatEvent:
    event_id: int
    session_id: str
    turn_id: str | None
    role: str
    kind: str
    content: str
    created_at: str
    metadata: dict[str, str] | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class MarimoChatStore:
    """SQL-backed session and event store using the configured tapestore database."""

    def __init__(
        self,
        url: str,
        *,
        sessions_table_name: str = "marimo_chat_sessions",
        events_table_name: str = "marimo_chat_events",
    ) -> None:
        self._url = url
        self._sessions_table_name = sessions_table_name
        self._events_table_name = events_table_name
        self._engine: Engine | None = None
        self._session_factory: sessionmaker_type | None = None
        self._sessions: Table | None = None
        self._events: Table | None = None
        self._lock = threading.RLock()

    def _ensure_initialized(self) -> None:
        if self._engine is not None and self._session_factory is not None and self._sessions is not None and self._events is not None:
            return

        metadata = MetaData()
        self._sessions = Table(
            self._sessions_table_name,
            metadata,
            Column("session_id", String(191), primary_key=True),
            Column("status", String(32), nullable=False),
            Column("active_turn_id", String(64), nullable=True),
            Column("last_event_id", BigInteger, nullable=False, default=0),
            Column("last_error", Text, nullable=True),
            Column("created_at", DateTime(timezone=False), nullable=False),
            Column("updated_at", DateTime(timezone=False), nullable=False),
        )
        self._events = Table(
            self._events_table_name,
            metadata,
            Column("event_id", BigInteger, primary_key=True, autoincrement=True),
            Column("session_id", String(191), nullable=False, index=True),
            Column("turn_id", String(64), nullable=True, index=True),
            Column("role", String(32), nullable=False),
            Column("kind", String(32), nullable=False),
            Column("content", Text, nullable=False),
            Column("metadata_json", Text, nullable=True),
            Column("created_at", DateTime(timezone=False), nullable=False),
        )
        self._engine = create_engine(self._url, pool_pre_ping=True)
        metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)

    def shutdown(self) -> None:
        if self._engine is not None:
            self._engine.dispose()

    def begin_turn(self, session_id: str, turn_id: str, content: str) -> tuple[SessionSnapshot, ChatEvent]:
        sessions = self._sessions_or_raise()
        with self._lock, self._session_factory_or_raise()() as session:
            now = _utcnow()
            row = session.execute(select(sessions).where(sessions.c.session_id == session_id)).first()
            if row and row.status == "running":
                raise TurnConflictError(f"session {session_id} already has a running turn")

            if row:
                session.execute(
                    sessions.update()
                    .where(sessions.c.session_id == session_id)
                    .values(
                        status="running",
                        active_turn_id=turn_id,
                        last_error=None,
                        updated_at=now,
                    )
                )
            else:
                session.execute(
                    sessions.insert().values(
                        session_id=session_id,
                        status="running",
                        active_turn_id=turn_id,
                        last_event_id=0,
                        last_error=None,
                        created_at=now,
                        updated_at=now,
                    )
                )

            event = self._append_event_locked(
                session,
                session_id=session_id,
                turn_id=turn_id,
                role="user",
                kind="message",
                content=content,
            )
            session.commit()
            snapshot = self._snapshot_locked(session, session_id)
            if snapshot is None:
                raise RuntimeError(f"marimo session {session_id} disappeared after begin_turn")
        return snapshot, event

    def append_event(
        self,
        *,
        session_id: str,
        turn_id: str | None,
        role: str,
        kind: str,
        content: str,
        metadata: dict[str, str] | None = None,
    ) -> ChatEvent:
        with self._lock, self._session_factory_or_raise()() as session:
            event = self._append_event_locked(
                session,
                session_id=session_id,
                turn_id=turn_id,
                role=role,
                kind=kind,
                content=content,
                metadata=metadata,
            )
            session.commit()
        return event

    def mark_running(self, session_id: str, turn_id: str) -> SessionSnapshot:
        return self._update_session_status(session_id, status="running", turn_id=turn_id, error=None)

    def mark_completed(self, session_id: str, turn_id: str) -> SessionSnapshot:
        return self._update_session_status(session_id, status="idle", turn_id=turn_id, error=None)

    def mark_failed(self, session_id: str, turn_id: str, error: str) -> SessionSnapshot:
        snapshot = self._update_session_status(session_id, status="failed", turn_id=turn_id, error=error)
        self.append_event(
            session_id=session_id,
            turn_id=turn_id,
            role="system",
            kind="error",
            content=error,
            metadata={"status": "failed"},
        )
        return self.get_session(session_id) or snapshot

    def record_webhook(
        self,
        *,
        session_id: str,
        turn_id: str | None,
        role: str,
        kind: str,
        content: str,
        status: str | None = None,
    ) -> tuple[SessionSnapshot | None, ChatEvent | None]:
        event = None
        if content:
            event = self.append_event(
                session_id=session_id,
                turn_id=turn_id,
                role=role,
                kind=kind,
                content=content,
                metadata={"source": "webhook"},
            )

        snapshot = None
        if status == "running" and turn_id is not None:
            snapshot = self.mark_running(session_id, turn_id)
        elif status == "completed" and turn_id is not None:
            snapshot = self.mark_completed(session_id, turn_id)
        elif status == "failed" and turn_id is not None:
            snapshot = self.mark_failed(session_id, turn_id, content or "Webhook marked turn as failed.")
        elif status == "idle":
            snapshot = self._update_session_status(session_id, status="idle", turn_id=turn_id, error=None)

        if snapshot is None:
            snapshot = self.get_session(session_id)
        return snapshot, event

    def get_session(self, session_id: str) -> SessionSnapshot | None:
        sessions = self._sessions_or_raise()
        with self._lock, self._session_factory_or_raise()() as session:
            row = session.execute(select(sessions).where(sessions.c.session_id == session_id)).first()
            if row is None:
                return None
            return self._row_to_snapshot(row)

    def list_events(self, session_id: str, after_event_id: int = 0, limit: int = 200) -> tuple[SessionSnapshot | None, list[ChatEvent]]:
        events = self._events_or_raise()
        with self._lock, self._session_factory_or_raise()() as session:
            snapshot = self._snapshot_locked(session, session_id)
            rows = session.execute(
                select(events)
                .where(events.c.session_id == session_id)
                .where(events.c.event_id > after_event_id)
                .order_by(events.c.event_id.asc())
                .limit(limit)
            ).all()
            return snapshot, [self._row_to_event(row) for row in rows]

    def active_turn_id_for_session(self, session_id: str) -> str | None:
        snapshot = self.get_session(session_id)
        if snapshot is None:
            return None
        return snapshot.active_turn_id

    def _update_session_status(self, session_id: str, *, status: str, turn_id: str | None, error: str | None) -> SessionSnapshot:
        sessions = self._sessions_or_raise()
        with self._lock, self._session_factory_or_raise()() as session:
            now = _utcnow()
            values: dict[str, object] = {
                "status": status,
                "updated_at": now,
                "last_error": error,
            }
            if status == "running":
                values["active_turn_id"] = turn_id
            elif turn_id is not None:
                values["active_turn_id"] = None
            session.execute(
                sessions.update().where(sessions.c.session_id == session_id).values(**values)
            )
            session.commit()
            snapshot = self._snapshot_locked(session, session_id)
            if snapshot is None:
                raise RuntimeError(f"marimo session {session_id} disappeared after status update")
            return snapshot

    def _append_event_locked(
        self,
        session,
        *,
        session_id: str,
        turn_id: str | None,
        role: str,
        kind: str,
        content: str,
        metadata: dict[str, str] | None = None,
    ) -> ChatEvent:
        events = self._events_or_raise()
        sessions = self._sessions_or_raise()
        now = _utcnow()
        session_row = session.execute(select(sessions).where(sessions.c.session_id == session_id)).first()
        if session_row is None:
            session.execute(
                sessions.insert().values(
                    session_id=session_id,
                    status="idle",
                    active_turn_id=None,
                    last_event_id=0,
                    last_error=None,
                    created_at=now,
                    updated_at=now,
                )
            )
        result = session.execute(
            events.insert().values(
                session_id=session_id,
                turn_id=turn_id,
                role=role,
                kind=kind,
                content=content,
                metadata_json=json.dumps(metadata, ensure_ascii=True) if metadata else None,
                created_at=now,
            )
        )
        event_id = int(result.inserted_primary_key[0])
        session.execute(
            sessions.update()
            .where(sessions.c.session_id == session_id)
            .values(last_event_id=event_id, updated_at=now)
        )
        return ChatEvent(
            event_id=event_id,
            session_id=session_id,
            turn_id=turn_id,
            role=role,
            kind=kind,
            content=content,
            created_at=now.isoformat(),
            metadata=metadata,
        )

    def _snapshot_locked(self, session, session_id: str) -> SessionSnapshot | None:
        sessions = self._sessions_or_raise()
        row = session.execute(select(sessions).where(sessions.c.session_id == session_id)).first()
        if row is None:
            return None
        return self._row_to_snapshot(row)

    def _row_to_snapshot(self, row) -> SessionSnapshot:
        return SessionSnapshot(
            session_id=row.session_id,
            status=row.status,
            active_turn_id=row.active_turn_id,
            last_event_id=int(row.last_event_id),
            updated_at=row.updated_at.replace(tzinfo=UTC).isoformat(),
            last_error=row.last_error,
        )

    def _row_to_event(self, row) -> ChatEvent:
        metadata_json = row.metadata_json
        metadata = json.loads(metadata_json) if metadata_json else None
        return ChatEvent(
            event_id=int(row.event_id),
            session_id=row.session_id,
            turn_id=row.turn_id,
            role=row.role,
            kind=row.kind,
            content=row.content,
            created_at=row.created_at.replace(tzinfo=UTC).isoformat(),
            metadata=metadata,
        )

    def _session_factory_or_raise(self) -> sessionmaker_type:
        self._ensure_initialized()
        if self._session_factory is None:
            raise RuntimeError("marimo chat session factory not initialized")
        return self._session_factory

    def _sessions_or_raise(self) -> Table:
        self._ensure_initialized()
        if self._sessions is None:
            raise RuntimeError("marimo chat sessions table not initialized")
        return self._sessions

    def _events_or_raise(self) -> Table:
        self._ensure_initialized()
        if self._events is None:
            raise RuntimeError("marimo chat events table not initialized")
        return self._events
