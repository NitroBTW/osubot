import aiosqlite
import datetime as dt
import logging
import os
import asyncio


from utils.config import DB_PATH

async def init_db() -> None:
    """Initialises the database
    
    Creates the databse file if it doesnt exist, creates table 'user_links'
    """
    # Create the database if it doesnt already exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    logging.info(f"Verified existence of database at {DB_PATH}")
    # Connect to the database with async
    async with aiosqlite.connect(DB_PATH) as db:
        logging.info(f"Connected to database at {DB_PATH}")
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
        logging.info("Created table 'user_links'")

async def set_link(discord_id: int, osu_user_id: int, osu_username: str, preferred_mode: int = 0 ,time_now: str = dt.datetime.utcnow().isoformat()) -> None:
    """
    Creates a link for a discord id to an osu profile, along with the time of link

    Args:
        discord_id (int): User's discord ID
        osu_user_id (int): The osu profile ID to be linked
        osu_username (str): The osu profile username to be linked
        preferred_mode (int, optional): The user's preferred mode, set here as default 0 (0 = osu, 1 = taiko, 2 = catch, 3 = mania)
        time_now (str, optional): The current time at which the link was created
    """
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
            (discord_id, osu_user_id, osu_username, preferred_mode, time_now,)
        )
        # Commit the changes to the database
        await db.commit()
        
async def get_link(discord_id: int):
    """Gets the osu! user link by Discord ID.
    
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
            osu_user_id, osu_username, preferred_mode = int(row[0]), str(row[1]), row[2]
            return osu_user_id, osu_username, preferred_mode