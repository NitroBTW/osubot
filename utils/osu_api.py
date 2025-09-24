"""
Script full of useful api calls for the osu!api
"""
import asyncio
import os
import httpx
from typing import Any, Optional
import logging

from ossapi import OssapiAsync

from utils.config import (
    OSU_CLIENT_ID, 
    OSU_CLIENT_SECRET, 
    BEATMAP_CACHE_DIR
)

logger = logging.getLogger(__name__)

class OsuClient:
    """
    Async wrapper for ossapi (osu! API v2) and rosu-pp for PP calculations
    """
    def __init__(self) -> None:
        """
        Initialise the async API client
        """
        # Ensure that a client ID and Secret are present for the osu!api
        if not OSU_CLIENT_ID or not OSU_CLIENT_SECRET:
            raise RuntimeError(
                "OSU_CLIENT_ID/OSU_CLIENT_SECRET not configured"
            )
        
        # Create the api and http clients
        self.api = OssapiAsync(OSU_CLIENT_ID, OSU_CLIENT_SECRET)
        self.http = httpx.AsyncClient(
            timeout=httpx.Timeout(12)
        )
        
        # Create the beatmap cache directory if it doesn't exist
        os.makedirs(BEATMAP_CACHE_DIR, exist_ok=True)
    
    async def get_user(
        self,
        identifier: str | int,
        mode: Optional[str] = None
    ) -> Any:
        """
        Get a user object by ID or Username

        Args:
            identifier (str | int): osu! user ID or username string
            mode (Optional[str], optional): Mode for getting stats. Defaults to None.

        Returns:
            Any: An ossapi user object.
        """
        # Try to get user data from the api
        try:
            # Check if we were given an integer (ID)
            if isinstance(identifier, int) or str(identifier).isdigit():
                # Return user data using the given ID
                return await self.api.user(int(identifier), mode=mode)
            
            # Return user data using a given Name
            return await self.api.user(str(identifier), mode=mode)
        except Exception as e:
            logger.error(f"Failed to get user data for {identifier}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get user data for {identifier}: {e}") from e
    
    async def get_score(
        self,
        score_id: int
    ) -> Optional[Any]:
        """
        Get score data from a given ID

        Args:
            score_id (int): The numerical ID of the osu! score

        Returns:
            Optional[Any]: ossapi score object.
        """
        return await self.api.score(score_id)
        
    async def get_recent_score(
        self,
        identifier: str | int,
        mode: Optional[str] = None,
        amount: Optional[int] = 1,
        include_fails: Optional[bool] = True,
    ) -> Optional[Any]:
        """
        Get the most recent score(s) for a user.

        Args:
            identifier (str | int): osu! user ID or Name
            mode (Optional[str], optional): Specify a mode. Defaults to None.
            amount (Optional[int], optional): How many of the user's recent scores to get. Defaults to 1.
            include_fails (Optional[bool], optional): Whether or not fails are included. Defaults to True.

        Returns:
            Optional[Any]: A list of ossapi Score objects or None.
        """
        # Get the user
        user = await self.get_user(identifier, mode)
        # Get that user's recent score(s)
        scores = await self.api.user_scores(
            user.id,
            "recent",
            mode=mode,
            limit=amount,
            include_fails=include_fails,
        )
        # Return None if no scores found
        if not scores:
            return None
        return scores
    
    async def get_top_scores(
        self,
        identifier: str | int,
        mode: Optional[str] = None,
        amount: int = 10,
    ) -> list[Any]:
        """
        Fetch the top 'amount' scores for a user

        Args:
            identifier (str | int): osu! user ID or Name
            mode (Optional[str], optional): Specify a mode. Defaults to None.
            amount (int, optional): How many of the user's top scores to get. Defaults to 10.

        Returns:
            list[Any]: A list of ossapi Score objects
        """
        # Get the user from the identifier
        user = await self.get_user(user, mode)
        # Ensure the amount is within the limits of the api
        amount = max(1, min(100, int(amount)))
        # Get that user's top scores
        scores = await self.api.user_scores(
            user.id,
            "best",
            mode=mode,
            limit=amount
        )
        # Return a list of scores (empty if no scores available)
        return list(scores or [])
    
    async def get_user_best_on_map(
        self,
        identifier: str | int,
        beatmap_id: int,
        mode: Optional[str] = None,
    ) -> list[Any]:
        """
        Fetch all scores by a user on a specific beatmap

        Args:
            identifier (str | int): osu! user ID or username
            beatmap_id (int): Numeric beatmap ID
            mode (Optional[str], optional): Specify a mode. Defaults to None.

        Returns:
            list[Any]: A list of ossapi BeatmapUserScore.score objects (sorted best-to-worst). Empty list if user has no scores on given beatmap.
        """
        # Get a user from the identifier given
        user = await self.get_user(identifier, mode)
        # Get the scores for that user on the given beatmap
        scores = await self.api.beatmap_user_scores(
            beatmap_id,
            user.id
        )
        if hasattr(scores, "scores"):
            return list(scores.scores)
        return list(scores or [])
    
    async def get_beatmap(
        self,
        beatmap_id: int
    ) -> Any:
        """
        Get a beatmap information by ID

        Args:
            beatmap_id (int): Numeric beatmap ID

        Returns:
            Any: Ossapi beatmap object
        """
        return await self.api.beatmap(beatmap_id)
    
    async def get_beatmapset(
        self,
        beatmapset_id: int,
    ) -> Any:
        """
        Get beatmapset information by ID

        Args:
            beatmapset_id (int): Numeric beatmapset ID

        Returns:
            Any: Ossapi beatmapset object
        """
        return await self.api.beatmapset(beatmapset_id)
    
    async def download_beatmap(
        self,
        beatmap_id: int,
    ) -> str:
        """
        Download a .osu file for the beatmap to cache and return local path.

        Args:
            beatmap_id (int): Numeric beatmap ID.

        Returns:
            str: Local filesystem path to the cached beatmap file
        """
        # Set the download path
        path = os.path.join(BEATMAP_CACHE_DIR, f"{beatmap_id}.osu")
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
        
        url = f"https://osu.ppy.sh/osu/{beatmap_id}"
        response = await self.http.get(url)
        response.raise_for_status()
        with open(path, "wb") as f:
            f.write(response.content)
        return path
        