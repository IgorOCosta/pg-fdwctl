import psycopg2
from psycopg2.extensions import connection, cursor
from typing import Optional


class PostgresConnection:
    def __init__(self, config: dict):
        self.config = config
        self.conn: Optional[connection] = None
        self.cursor: Optional[cursor] = None

    def connect(self) -> None:
        if self.conn is not None:
            return

        self.conn = psycopg2.connect(
            host=self.config["host"],
            port=self.config["port"],
            dbname=self.config["database"],
            user=self.config["user"],
            password=self.config["password"]
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def execute(self, query: str, params=None) -> None:
        self.connect()
        assert self.cursor is not None  # 🔒 garante para o type checker
        self.cursor.execute(query, params or ())

    def fetchone(self):
        assert self.cursor is not None
        return self.cursor.fetchone()

    def fetchall(self):
        assert self.cursor is not None
        return self.cursor.fetchall()

    def notice_flush(self) -> None:
        assert self.conn is not None
        while self.conn.notices:
            print(f"📣 NOTICE: {self.conn.notices.pop(0).strip()}")

    def close(self) -> None:
        if self.cursor is not None:
            self.cursor.close()
        if self.conn is not None:
            self.conn.close()
