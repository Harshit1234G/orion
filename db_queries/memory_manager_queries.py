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

DROP_TABLE = 'DROP TABLE IF EXISTS '

RESET_TABLE = 'DELETE FROM '

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
CREATE TABLE IF NOT EXISTS long_term_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE,
    content TEXT NOT NULL,
    category TEXT,
    importance INTEGER DEFAULT 5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    is_active BOOLEAN DEFAULT 1
)
'''

SAVE_LONG_TERM_MEMORY = '''
INSERT INTO long_term_memory (key, content, category, importance, expires_at)
VALUES (?, ?, ?, ?, ?)
'''

RETRIEVE_FROM_ID = '''
SELECT *
FROM long_term_memory
WHERE id = ?
'''

RETRIEVE_FROM_KEY = '''
SELECT *
FROM long_term_memory
WHERE key = ?
'''

DELETE_LONG_TERM_MEMORY = '''
DELETE FROM long_term_memory
WHERE key = ?
'''

GET_ALL_KEYS = '''
SELECT key
FROM long_term_memory
'''

UPDATE_LAST_ACCESSED_AT = '''
UPDATE long_term_memory
SET last_accessed_at = CURRENT_TIMESTAMP
WHERE key = ?
'''

# ------------------------------
# Environemnt memory
# ------------------------------
ENVIRONMENT_MEMORY_CREATE_TABLE = '''
CREATE TABLE IF NOT EXISTS environment_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    metadata TEXT DEFAULT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, key)
)
'''

SAVE_ENVIRONMENT_MEMORY = '''
INSERT INTO environment_memory (category, key, value, metadata)
VALUES (?, ?, ?, ?)
ON CONFLICT(category, key)
DO UPDATE SET 
    value = excluded.value,
    metadata = COALESCE(excluded.metadata, environment_memory.metadata),
    updated_at = CURRENT_TIMESTAMP
'''

RETRIEVE_ENVIRONMENT = 'SELECT * FROM environment_memory'

RETRIEVE_ENVIRONMENT_MEMORY_CATEGORY = '''
SELECT * FROM environment_memory
WHERE category = ?
'''

DELETE_ENVIRONMENT_MEMORY = '''
DELETE FROM environment_memory
WHERE category = ? AND key = ?
'''
