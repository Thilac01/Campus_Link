"""SQLite storage and migrations for Phase 1."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Profile:
    display_name: str
    university_email: str = ""
    department: str = ""
    academic_year: str = ""
    device_nickname: str = ""
    profile_image: str = ""


@dataclass(frozen=True, slots=True)
class ChatRecord:
    message_id: str
    peer_device_id: str
    direction: str
    body: str
    status: str
    created_at: str


class Database:
    """Owns the single local SQLite connection used by the UI process."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._connection: sqlite3.Connection | None = None

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(self.path)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA journal_mode = WAL")
        return self._connection

    def initialize(self) -> None:
        schema_path = Path(__file__).with_name("schema.sql")
        with self.connection:
            self.connection.executescript(schema_path.read_text(encoding="utf-8"))
            self.connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version) VALUES (1)"
            )

    def get_profile(self) -> Profile | None:
        row = self.connection.execute("SELECT * FROM local_profile WHERE id = 1").fetchone()
        if row is None:
            return None
        return Profile(
            display_name=row["display_name"],
            university_email=row["university_email"],
            department=row["department"],
            academic_year=row["academic_year"],
            device_nickname=row["device_nickname"],
            profile_image=row["profile_image"],
        )

    def save_profile(self, profile: Profile) -> None:
        name = profile.display_name.strip()
        if not name or len(name) > 80:
            raise ValueError("Display name must contain between 1 and 80 characters")
        with self.connection:
            self.connection.execute(
                """INSERT INTO local_profile(
                       id, display_name, university_email, department, academic_year,
                       device_nickname, profile_image
                   ) VALUES (1, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                       display_name=excluded.display_name,
                       university_email=excluded.university_email,
                       department=excluded.department,
                       academic_year=excluded.academic_year,
                       device_nickname=excluded.device_nickname,
                       profile_image=excluded.profile_image,
                       updated_at=CURRENT_TIMESTAMP""",
                (
                    name,
                    profile.university_email.strip(),
                    profile.department.strip(),
                    profile.academic_year.strip(),
                    profile.device_nickname.strip(),
                    profile.profile_image,
                ),
            )

    def save_chat_message(
        self,
        peer_device_id: str,
        peer_name: str,
        direction: str,
        body: str,
        status: str,
        message_id: str | None = None,
    ) -> str:
        if direction not in {"incoming", "outgoing"}:
            raise ValueError("Invalid message direction")
        if not body.strip() or len(body) > 65_536:
            raise ValueError("Message body must contain between 1 and 65,536 characters")
        conversation_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"campuslink:{peer_device_id}"))
        identifier = message_id or str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()
        with self.connection:
            self.connection.execute(
                """INSERT INTO devices(id, nickname, public_key_fingerprint)
                   VALUES (?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET nickname=excluded.nickname""",
                (peer_device_id, peer_name, f"pending:{peer_device_id}"),
            )
            self.connection.execute(
                """INSERT OR IGNORE INTO conversations(id, kind, title)
                   VALUES (?, 'direct', ?)""",
                (conversation_id, peer_name),
            )
            sequence = self.connection.execute(
                """SELECT COALESCE(MAX(sequence_number), 0) + 1
                   FROM messages WHERE conversation_id=?""",
                (conversation_id,),
            ).fetchone()[0]
            self.connection.execute(
                """INSERT OR IGNORE INTO messages(
                       id, conversation_id, sender_device_id, body, status,
                       sequence_number, created_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    identifier,
                    conversation_id,
                    peer_device_id if direction == "incoming" else None,
                    body.strip(),
                    status,
                    sequence,
                    created_at,
                ),
            )
        return identifier

    def update_message_status(self, message_id: str, status: str) -> None:
        with self.connection:
            self.connection.execute("UPDATE messages SET status=? WHERE id=?", (status, message_id))

    def chat_history(self, peer_device_id: str, limit: int = 500) -> list[ChatRecord]:
        conversation_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"campuslink:{peer_device_id}"))
        rows = self.connection.execute(
            """SELECT m.id, m.sender_device_id, m.body, m.status, m.created_at
               FROM messages m WHERE m.conversation_id=?
               ORDER BY m.sequence_number DESC LIMIT ?""",
            (conversation_id, min(max(limit, 1), 2_000)),
        ).fetchall()
        return [
            ChatRecord(
                message_id=row["id"],
                peer_device_id=peer_device_id,
                direction="incoming" if row["sender_device_id"] else "outgoing",
                body=row["body"],
                status=row["status"],
                created_at=row["created_at"],
            )
            for row in reversed(rows)
        ]

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
