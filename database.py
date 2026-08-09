import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "cpm.db"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_package(name):
    with connect() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM packages
            WHERE name = ?
            """,
            (name,)
        ).fetchone()

    return row


def list_packages():
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM packages
            ORDER BY name
            """
        ).fetchall()

    return rows
