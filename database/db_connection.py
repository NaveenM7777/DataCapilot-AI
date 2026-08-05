import sqlite3
import pandas as pd

# Path to the SQLite database
DB_PATH = "database/chinook.db"


def get_connection():
    """
    Creates and returns a connection to the SQLite database.
    """

    conn = sqlite3.connect(DB_PATH)

    return conn


def get_schema():
    """
    Returns all table names and column names
    in a readable format.
    """

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

    tables = cursor.fetchall()

    schema = ""

    for table in tables:

        table_name = table[0]

        cursor.execute(f"PRAGMA table_info({table_name});")

        columns = cursor.fetchall()

        column_names = [column[1] for column in columns]

        schema += f"\nTable: {table_name}\n"

        schema += "Columns: " + ", ".join(column_names) + "\n"

    conn.close()

    return schema


def run_query(sql_query):
    """
    Executes a SQL query
    and returns the result as a DataFrame.
    """

    conn = get_connection()

    df = pd.read_sql_query(sql_query, conn)

    conn.close()

    return df