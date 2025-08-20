import sqlite3

class DB:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.execute("CREATE TABLE IF NOT EXISTS used (id TEXT PRIMARY KEY)")
        self.conn.commit()

    def is_used(self, gid):
        cur = self.conn.execute("SELECT 1 FROM used WHERE id=?", (gid,))
        return cur.fetchone() is not None

    def mark_used(self, gid):
        self.conn.execute("INSERT OR IGNORE INTO used (id) VALUES (?)", (gid,))
        self.conn.commit()
