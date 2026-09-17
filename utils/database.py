# utils/database.py
import pandas as pd
from core.database import engine
from core.logger import log_action

def connect_to_db():
    """Connect to the database and verify the connection"""
    try:
        with engine.connect() as connection:
            log_action("db", "Database connection verified successfully!")
            return True
    except Exception as e:
        log_action("db", f"Error connecting to database: {e}", level="error")
        return False

def read_table(table_name, limit=None):
    """Read data from a specified table in the database"""
    try:
        if limit:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            df = pd.read_sql(query, engine)
        else:
            df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
        
        log_action("db", f"Successfully read {df.shape[0]} rows from '{table_name}'")
        return df
    except Exception as e:
        log_action("db", f"Error reading from table '{table_name}': {e}", level="error")
        return None
