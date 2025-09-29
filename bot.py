"""
Main script for running the discord bot
"""
import asyncio
import logging
from typing import List

import discord
from discord.ext import commands

from utils.config import DISCORD_BOT_TOKEN
from utils.database import init_db
from utils.osu_api import OsuClient
from oauth_server import OAuthServer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class DiscordBot(commands.Bot):
    """
    Custom discord bot that holds database and other shared instances

    Args:
        commands (discord.Bot): Discord bot class to inherit from
    """
    def __init__(self) -> None:
        """Initialise the bot with intents and api client
        """
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            intents=intents,
            command_prefix="-",
            help_command=None
        )
        self.osu_client: OsuClient | None = None
        self.oauth: OAuthServer | None = None
        self._cogs_loaded = False
    
    async def setup_hook(self):
        """
        Called by discord on startup. Initialise the Database, Osu client, and load cogs.
        """
        logger.info("Bot setup_hook starting")
        await init_db()
        self.osu_client = OsuClient()
        self.oauth = OAuthServer(self)
        await self.oauth.start()


        cogs: List[str] = [
            "cogs.link",
        ]

        for c in cogs:
            try:
                await self.load_extension(c)
                logger.info(f"Successfully loaded cog {c}")
            except Exception as e:
                logger.error(f"Failed to load cog {c}: {e}", exc_info=True)
        
    async def on_ready(self) -> None:
        """
        Called on bot login
        """
        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        
        # Sync commands globally (for DMs and all guilds)
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} global commands: {[cmd.name for cmd in synced]}")
        except Exception as e:
            logger.error(f"Global command sync failed: {e}")
        
        # Also sync to specific guild for instant testing
        guild_id = 1407837272165978253
        try:
            guild = discord.Object(id=guild_id)
            guild_synced = await self.tree.sync(guild=guild)
            logger.info(f"Synced {len(guild_synced)} commands to guild {guild_id}: {[cmd.name for cmd in guild_synced]}")
        except discord.HTTPException as e:
            logger.error(f"Guild command sync failed (HTTP {e.status}): {e.text}")
        except Exception as e:
            logger.error(f"Guild command sync failed: {e}")
    
    async def close(self) -> None:
        """
        Gracefully close discord bot and osu client
        """
        if self.osu_client:
            await self.osu_client.close()
        await super().close()

def main() -> None:
    """
    Entry point for running the bot
    """
    osubot = DiscordBot()
    osubot.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()