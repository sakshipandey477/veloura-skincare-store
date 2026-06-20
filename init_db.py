import sqlite3

conn = sqlite3.connect("veloura.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    image TEXT
)
""")

conn.execute("DELETE FROM users WHERE username='admin'")

conn.execute("""
INSERT INTO users (username, password, role)
VALUES ('admin', '1234', 'admin')
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    username TEXT,
    quantity INTEGER DEFAULT 1,
    FOREIGN KEY (product_id) REFERENCES products(id)
)
""")
conn.commit()

users = conn.execute("SELECT username, password, role FROM users").fetchall()
print(users)

conn.close()

print("Database created successfully")