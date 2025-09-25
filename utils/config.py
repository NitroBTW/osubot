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
OSU_REDIRECT_URI: str = os.getenv("OSU_REDIRECT_URI", "")
OAUTH_HOST: str = os.getenv("OAUTH_HOST", "127.0.0.1")
OAUTH_PORT: int = os.getenv("OAUTH_PORT", "8080")
HTTP_TIMEOUT_SECONDS: int = os.getenv("HTTP_TIMEOUT_SECONDS", "300")