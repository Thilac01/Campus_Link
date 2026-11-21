CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS local_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    display_name TEXT NOT NULL CHECK(length(display_name) BETWEEN 1 AND 80),
    university_email TEXT NOT NULL DEFAULT '', department TEXT NOT NULL DEFAULT '',
    academic_year TEXT NOT NULL DEFAULT '', device_nickname TEXT NOT NULL DEFAULT '',
    profile_image TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY, display_name TEXT NOT NULL, email TEXT, department TEXT,
    verification_state TEXT NOT NULL DEFAULT 'unverified'
);
CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY, user_id TEXT REFERENCES users(id), nickname TEXT NOT NULL,
    public_key_fingerprint TEXT NOT NULL UNIQUE, last_seen_at TEXT
);
CREATE TABLE IF NOT EXISTS trusted_peers (
    device_id TEXT PRIMARY KEY REFERENCES devices(id), trust_state TEXT NOT NULL,
    verified_at TEXT, blocked_at TEXT
);
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY, kind TEXT NOT NULL, title TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id),
    sender_device_id TEXT REFERENCES devices(id), body TEXT NOT NULL, status TEXT NOT NULL,
    sequence_number INTEGER NOT NULL, created_at TEXT NOT NULL, edited_at TEXT,
    UNIQUE(conversation_id, sequence_number)
);
CREATE TABLE IF NOT EXISTS message_receipts (
    message_id TEXT NOT NULL REFERENCES messages(id), device_id TEXT NOT NULL REFERENCES devices(id),
    state TEXT NOT NULL, occurred_at TEXT NOT NULL, PRIMARY KEY(message_id, device_id, state)
);
CREATE TABLE IF NOT EXISTS groups (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
    owner_user_id TEXT REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS group_members (
    group_id TEXT NOT NULL REFERENCES groups(id), user_id TEXT NOT NULL REFERENCES users(id),
    role TEXT NOT NULL, joined_at TEXT NOT NULL, PRIMARY KEY(group_id, user_id)
);
CREATE TABLE IF NOT EXISTS transfers (
    id TEXT PRIMARY KEY, peer_device_id TEXT REFERENCES devices(id), direction TEXT NOT NULL,
    display_name TEXT NOT NULL, total_size INTEGER NOT NULL CHECK(total_size >= 0),
    transferred_size INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL,
    manifest_hash TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transfer_chunks (
    transfer_id TEXT NOT NULL REFERENCES transfers(id), offset_bytes INTEGER NOT NULL,
    size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL, verified INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(transfer_id, offset_bytes)
);
CREATE TABLE IF NOT EXISTS file_manifests (
    transfer_id TEXT NOT NULL REFERENCES transfers(id), relative_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL, sha256 TEXT, PRIMARY KEY(transfer_id, relative_path)
);
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY, peer_device_id TEXT REFERENCES devices(id), session_type TEXT NOT NULL,
    consent_state TEXT NOT NULL, started_at TEXT, ended_at TEXT
);
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY, category TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL, peer_device_id TEXT,
    details_json TEXT NOT NULL DEFAULT '{}', occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
