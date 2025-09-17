"""
Config file for getting environment variables and setting defaults for missing values where possible
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Discord credentials
DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")

# Database configuration
DB_PATH: str = os.getenv("DB_PATH", "./data/database.db")
BEATMAP_CACHE_DIR: str = os.getenv("BEATMAP_CACHE_DIR", "./cache")

# Osu credentials
OSU_CLIENT_ID: str = os.getenv("OSU_CLIENT_ID", "")
OSU_CLIENT_SECRET: str = os.getenv("OSU_CLIENT_SECRET", "")

# Oauth configuration