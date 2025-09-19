"""
Functions for using the database.
"""
import aiosqlite
import datetime as dt
import logging
import os
import asyncio

from utils.config import DB_PATH
from typing import Optional

logger = logging.getLogger(__name__)

async def init_db() -> None:
    """
    Initialises the SQLite database
    
    Creates the databse file if it doesn't exist, and ensure's required tables exist.
    """
    # Create the database if it doesnt already exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    logger.info(f"Ensured database at {DB_PATH}")
    
    # Connect to the database with async
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_links (
                discord_id INTEGER PRIMARY KEY,
                osu_user_id INTEGER NOT NULL,
                osu_username TEXT NOT NULL,
                linked_at TEXT NOT NULL,
                preferred_mode TEXT
            )
            """
        )
        await db.commit()
        logger.info(f"Initialised database schema at {DB_PATH}.")
        
        

async def set_link(
        discord_id: int, 
        osu_user_id: int, 
        osu_username: str, 
        preferred_mode: str = "osu",
        linked_at: Optional[str] = None
    ) -> None:
    """
    Creates or updates an osu! link for a Discord user.

    Args:
        discord_id (int): User's discord ID.
        osu_user_id (int): The osu profile ID to be linked.
        osu_username (str): The osu profile username to be linked.
        preferred_mode (str, optional): The user's preferred mode (osu | taiko | fruits | mania).
        linked_at (str, optional): The time at which the link was created.
    
    Raises:
        ValueError: If preferred mode is not one of (osu | taiko | fruits | mania)
    """
    # Validate preferred_mode
    if preferred_mode not in ["osu", "taiko", "fruits", "mania"]:
        raise ValueError(
            f"preferred_mode must be one of (osu | taiko | fruits | mania), got {preferred_mode!r}"
        )
        
    # Set 'linked_at' to current time if not defined.
    if linked_at is None:
        linked_at = dt.datetime.utcnow().isoformat()
        logger.info(f"'linked_at' was not provided, setting linked_at to {linked_at}.")
        
    # Connect to the database
    async with aiosqlite.connect(DB_PATH) as db:
        # Insert the user's link data
        await db.execute(
            """
            INSERT INTO user_links (discord_id, osu_user_id, osu_username, preferred_mode, linked_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (discord_id) DO UPDATE SET
                osu_user_id=excluded.osu_user_id,
                osu_username=excluded.osu_username,
                preferred_mode=excluded.preferred_mode,
                linked_at=excluded.linked_at
            """,
            (discord_id, osu_user_id, osu_username, preferred_mode, linked_at)
        )
        # Commit the changes to the database
        await db.commit()
        logger.info(f"Successfully added link for Discord ID: {discord_id} to the database.")
        
async def get_link(discord_id: int):
    """
    Gets the osu! link by Discord ID.
    
    Fetches the osu! user ID, username, and preferred mode associated with the given Discord user ID.
    
    Args:
        discord_id (int): The Discord ID of the user to search for.
    
    Returns:
        Optional[tuple[int, str, int]]: a tuple of (osu_user_id, osu_username, preferred mode)
        if found; otherwise None.
    """
    # Connect to the database
    async with aiosqlite.connect(DB_PATH) as db:
        # Search for a match to the given discord ID
        async with db.execute(
            """
            SELECT osu_user_id, osu_username, preferred_mode
            FROM user_links
            WHERE discord_id = ?
            """,
            (discord_id,)
        ) as cursor:
            # Get the row where a match is found
            row = await cursor.fetchone()
            # Return None if no match is found
            if not row:
                return None
            # Create and return a tuple with the found data
            osu_user_id, osu_username, preferred_mode = int(row[0]), str(row[1]), str(row[2])
            return osu_user_id, osu_username, preferred_mode