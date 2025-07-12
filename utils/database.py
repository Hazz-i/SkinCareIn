from sqlalchemy import create_engine
import pandas as pd

from dotenv import load_dotenv
import os

load_dotenv()

# Database configuration from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "skinsight_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# uri = "mariadb+mariadbconnector://john.doe:itsasecret@mariadb.example.com/mydatabase"

# Create engine with MariaDB optimizations
engine = create_engine(DATABASE_URL)

def connect_to_db():
    """
    Connect to the database and verify the connection
    
    Returns:
    --------
    bool
        True if connection successful, False otherwise
    """
    try:
        # Check connection
        connection = engine.connect()
        connection.close()
        print("Database connection successful!")
        return True
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False

# Function to read data from table
def read_table(table_name, limit=None):
    """
    Read data from a specified table in the database
    
    Parameters:
    -----------
    table_name : str
        Name of the table to read
    limit : int, optional
        Limit the number of rows returned
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing the table data
    """
    try:
        if limit:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            df = pd.read_sql(query, engine)
        else:
            df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
        
        print(f"Successfully read {df.shape[0]} rows from '{table_name}'")
        return df
    
    except Exception as e:
        print(f"Error reading from table '{table_name}': {e}")
        return None
    
    
