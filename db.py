import sqlite3
from datetime import datetime

conn = sqlite3.connect("finance.db")

cursor = conn.cursor()

def insert(table: str, column_values: dict):
    columns = ', '.join(column_values.keys())
    values = [tuple(column_values.values())]
    placeholders = ", ".join( "?" * len(column_values.keys()) )
    cursor.executemany(
        f"INSERT INTO {table} "
        f"({columns}) "
        f"VALUES ({placeholders})",
        values)
    conn.commit()

def delete(table: str, condition: str) -> None:
    query = f"DELETE FROM {table} WHERE {condition}"
    cursor.execute(query)
    conn.commit()

def get_cursor():
    return cursor

def init_db():
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='expense'")
    if not cursor.fetchall():
        with open("createdb.sql", "r") as f:
            sql = f.read()
        cursor.executescript(sql)

        categories = [
            ("транспорт",),
            ("продукты",),
            ("кафе",),
            ("связь",),
            ("развлечения",),
            ("дом",),
            ("прочее",)
        ]

        cursor.executemany("INSERT INTO category (name) VALUES (?)", categories)

        conn.commit()

init_db()

