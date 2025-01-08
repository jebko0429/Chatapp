import sqlite3

conn = sqlite3.connect("users.db")
c = conn.cursor()

# Drop the old users table
c.execute("DROP TABLE IF EXISTS users")

# Recreate the users table with the new schema
c.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    status TEXT DEFAULT 'pending'
)
""")

conn.commit()
conn.close()
print("Users table recreated successfully.")
