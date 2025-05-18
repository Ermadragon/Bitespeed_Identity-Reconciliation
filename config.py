from sqlalchemy.engine import URL
from dotenv import load_dotenv
import os

load_dotenv()

driver_name = os.getenv('driver_name')
server = os.getenv('server')
database_name = os.getenv('database_name')
uid = os.getenv('uid')
password = os.getenv('password')

connection_string = f"DRIVER={driver_name};SERVER={server};DATABASE={database_name};UID={uid};PWD={password}"

connection_url = URL.create(
    "mssql+pyodbc", query={"odbc_connect": connection_string}
)
