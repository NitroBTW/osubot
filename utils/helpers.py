"""
Helper functions for use/continuity throughout osu!bot
"""
import logging
from typing import Any
from pathlib import Path

from utils.config import (
    BEATMAP_CACHE_DIR
)

logger = logging.getLogger(__name__)

def api_mods_to_string(mods: list[Any]) -> str:
    """
    Convert an osu!api mods list to an acronym string like 'HDDT'

    Args:
        mods (List[Any]): A list of mod dicts or objects with 'acronym'.

    Returns:
        str: Concatenated mod acronyms, e.g., 'HDDT', Empty string if none.
    """
    # Try and get acronyms if there are any
    try:
        # Initiate an empty list for acronyms
        acronyms = []
        # Go through the mods in the list
        for mod in mods or []:
            # Check if we have a dictionary with 'acronym' object
            if isinstance(mod, dict) and "acronym" in mod:
                acronyms.append(mod["acronym"].upper())
            # Otherwise get 'acronym' object if it exists, or default to None
            else:
                acronym = getattr(mod, "acronym", None)
                # If there's an acronym, append it to the mod string
                if acronym:
                    acronyms.append(str(acronym).upper())
        # Attach the list of acronyms into a string
        return "".join(acronyms)
    # Return an empty string if no acronyms are found
    except Exception:
        return ""

def delete_beatmap(beatmap_id: int) -> bool:
    """
    Delete a beatmap from the cache.

    Args:
        beatmap_id (int): Numeric beatmap ID.

    Returns:
        bool: True if the file was deleted, False if it didn't exist or an error occurred.
    """
    if beatmap_id <= 0:
        logger.warning(f"Invalid beatmap_id: {beatmap_id}")
        return False

    path = Path(BEATMAP_CACHE_DIR) / f"{beatmap_id}.osu"

    if not path.exists():
        logger.warning(f"Beatmap {beatmap_id} does not exist in cache.")
        return False

    try:
        path.unlink()
        logger.info(f"Successfully deleted beatmap {beatmap_id} from cache.")
        return True
    except OSError as e:
        logger.error(f"Failed to delete beatmap {beatmap_id} from cache: {e}")
        return False