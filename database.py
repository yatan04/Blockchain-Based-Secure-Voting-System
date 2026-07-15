import sqlite3
import os

DB_NAME = "voting.db"

def get_db():
    """Return a connection to the SQLite database."""
    return sqlite3.connect(DB_NAME)

def setup_database():
    # Connect or create DB
    conn = get_db()
    cursor = conn.cursor()

    print("Connected to database:", DB_NAME)

    # Create Voters Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            voter_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            has_voted INTEGER
        )
    """)

    # Create Candidates Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            candidate_id TEXT PRIMARY KEY,
            name TEXT,
            party TEXT,
            vote_count INTEGER
        )
    """)

    # Create Users Table (for login)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Create Blockchain Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            index_no INTEGER PRIMARY KEY,
            timestamp REAL,
            transactions TEXT,
            previous_hash TEXT,
            nonce INTEGER,
            hash TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == "__main__":
    setup_database()

    # Confirm file exists
    if os.path.exists(DB_NAME):
        print("SUCCESS ✔ Created:", DB_NAME)
    else:
        print("ERROR ❌ Database was NOT created!")
