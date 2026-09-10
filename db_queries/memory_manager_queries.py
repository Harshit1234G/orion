# ------------------------------
# Conversation memory
# ------------------------------
CONVERSATION_MEMORY_CREATE_TABLE = '''
CREATE TABLE IF NOT EXISTS conversation_events(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
'''

DROP_TABLE = 'DROP TABLE IF EXISTS ?'

SAVE_CONVERSATION = '''
INSERT INTO conversation_events (role, content)
VALUES (?, ?)
'''

RETRIEVE_CONVERSATION = '''
SELECT *
FROM conversation_events
ORDER BY id DESC
LIMIT ?
'''

DELETE_CONVERSATION = '''
DELETE FROM conversation_events
WHERE id = ?
'''

# ------------------------------
# Long term memory
# ------------------------------
LONG_TERM_MEMORY_CREATE_TABLE = '''
CREATE TABLE long_term_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE,
    content TEXT NOT NULL,
    category TEXT
    importance INTEGER DEFAULT 5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at DATETIME,
    expires_at DATETIME
    is_active INTEGER DEFAULT 1
)
'''