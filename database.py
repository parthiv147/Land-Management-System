from mysql.connector.pooling import MySQLConnectionPool
import os
from dotenv import load_dotenv
load_dotenv()
# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'admin'),
    'db': os.getenv('DB_NAME', 'land'),
    'pool_name': 'login',
    'pool_size': 3,
    'pool_reset_session': True
}

# Create database connection pool
conn_pool = MySQLConnectionPool(**DB_CONFIG)

def get_connection():
    """Get a connection from the connection pool."""
    return conn_pool.get_connection()

def execute_query(query, params=None, fetch_one=False, commit=False):
    """
    Execute a SQL query.

    Args:
        query (str): The SQL query to execute.
        params (tuple): Parameters to pass to the query (optional).
        fetch_one (bool): Whether to fetch only one row (optional).
        commit (bool): Whether to commit the transaction (optional).

    Returns:
        tuple or list: Query results for select or None for DML operations.
    """
    conn = None
    cursor = None
    result = None
    
    try:
        conn = get_connection()
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute(query, params)

        if commit:
            conn.commit()  # Commit the transaction if needed
            result = None  # Typically for DML operations, a result is not needed
        elif fetch_one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()

    except Exception as e:
        print(f"Error executing query: {e}")
        if conn:
            conn.rollback()  # Rollback in case of error
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return result
