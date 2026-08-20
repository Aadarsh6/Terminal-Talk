import sqlite3

def init_db(filename):
    connection = sqlite3.connect(filename)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint TEXT NOT NULL,
        direction TEXT NOT NULL,
        text TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.commit()
    connection.close()

def save_message(filename, fingerprint, direction, text):
    connection = sqlite3.connect(filename)

    connection.execute(
        """
        INSERT INTO messages (fingerprint, direction, text)
        VALUES(?, ?, ?)
        """,
        (fingerprint, direction, text)
    )
    connection.commit()
    connection.close()

def load_messages(filename, fingerprint):
    connection = sqlite3.connect(filename)

    result = connection.execute(
        """
        SELECT direction, text, timestamp
        FROM messages
        WHERE fingerprint = ?
        ORDER BY timestamp
        """,
        (fingerprint,)
    )
    messages = result.fetchall()
    connection.close()

    return messages






# ! for test

if __name__ == "__main__":
    db = "test_history.db"

    fingerprint = "A1B2:C3D4:E5F6"

    init_db(db)

    save_message(db, fingerprint, "sent", "Hello!")
    save_message(db, fingerprint, "received", "Hey!")
    save_message(db, fingerprint, "sent", "How are you?")

    messages = load_messages(db, fingerprint)

    for message in messages:
        print(message)