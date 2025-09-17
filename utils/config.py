import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH: str = os.getenv("DB_PATH", "./data/database.db")