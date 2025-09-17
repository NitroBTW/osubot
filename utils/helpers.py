"""
Helper functions for use/continuity throughout osu!bot
"""

def api_mods_to_string(mods: List[Any]) -> str:
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