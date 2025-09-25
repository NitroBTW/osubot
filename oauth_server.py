"""
Minimal aiohttp server to handle osu! OAuth linking.

Routes:
  - GET /osu/callback  -> OAuth redirect handler
"""
import asyncio
import urllib.parse
from typing import Optional

import aiohttp
from aiohttp import web

from utils.config import (
    OSU_CLIENT_ID,
    OSU_CLIENT_SECRET,
    OSU_REDIRECT_URI,
    OAUTH_HOST,
    OAUTH_PORT,
    HTTP_TIMEOUT_SECONDS,
)
from utils.database import create_oauth_state, pop_oauth_state, set_link

import logging

logger = logging.getLogger(__name__)

class OAuthServer:

    def __init__(self, bot) -> None:
        """
        Initialize the OAuth server.

        Args:
            bot: The running discord.py Bot instance for DM notifications.
        """
        self.bot = bot
        self._app = web.Application()
        self._app.add_routes([web.get("/osu/callback", self.handle_callback)])
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._http = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
        )

    async def start(self) -> None:
        """
        Start the aiohttp server.
        """
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, host=OAUTH_HOST, port=OAUTH_PORT)
        await self._site.start()
        logger.info(f"OAuth server listening on http://{OAUTH_HOST}:{OAUTH_PORT}")

    async def stop(self) -> None:
        """
        Stop the server and close HTTP session.
        """
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()
        await self._http.close()
        logger.info("OAuth server stopped.")

    async def authorize_url_for(self, discord_id: int) -> str:
        """
        Create a state and return an osu! authorization URL for the user.

        Args:
            discord_id (int): The Discord ID to associate with the authorization URL.

        Returns:
            str: The osu! authorization URL with the generated state.
        """
        state = await create_oauth_state(discord_id)
        logger.info(f"Generated OAuth authorization URL for Discord ID {discord_id}")
        q = {
            "client_id": str(OSU_CLIENT_ID),
            "redirect_uri": OSU_REDIRECT_URI,
            "response_type": "code",
            "scope": "public",
            "state": state,
        }
        return "https://osu.ppy.sh/oauth/authorize?" + urllib.parse.urlencode(q)

    async def handle_callback(self, request: web.Request) -> web.Response:
        """
        Handle osu! OAuth redirect: exchange code for token, fetch user info, and link account.

        Args:
            request (web.Request): The incoming aiohttp web request containing query parameters.

        Returns:
            web.Response: HTTP response indicating success or error.
        """
        code = request.query.get("code")
        state = request.query.get("state")

        if not code or not state:
            logger.warning("OAuth callback missing code or state")
            return web.Response(text="Missing code/state.", status=400)

        discord_id = await pop_oauth_state(state)
        if not discord_id:
            logger.warning(f"Invalid or expired OAuth state: {state}")
            return web.Response(text="Invalid or expired state.", status=400)

        # Exchange code for token
        token_url = "https://osu.ppy.sh/oauth/token"
        data = {
            "client_id": str(OSU_CLIENT_ID),
            "client_secret": OSU_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": OSU_REDIRECT_URI,
        }
        async with self._http.post(token_url, data=data) as resp:
            if resp.status != 200:
                body = await resp.text()
                return web.Response(
                    text=f"Token exchange failed: {resp.status}\n{body}",
                    status=500,
                )
            tok = await resp.json()
            logger.info(f"Successfully exchanged token for Discord ID {discord_id}")

        access_token = tok.get("access_token")
        if not access_token:
            logger.error(f"No access token received for Discord ID {discord_id}")
            return web.Response(text="No access token.", status=500)

        # Get authenticated user
        me_url = "https://osu.ppy.sh/api/v2/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with self._http.get(me_url, headers=headers) as resp:
            if resp.status != 200:
                body = await resp.text()
                return web.Response(
                    text=f"/me failed: {resp.status}\n{body}", status=500
                )
            me = await resp.json()
            logger.info(f"Successfully fetched osu! user info for Discord ID {discord_id}")

        osu_id = int(me["id"])
        osu_name = str(me["username"])
        await set_link(discord_id, osu_id, osu_name)
        logger.info(f"Linked Discord ID {discord_id} to osu! user '{osu_name}' (ID {osu_id})")

        # Try DM the user (non-fatal if it fails)
        try:
            user = self.bot.get_user(discord_id) or await self.bot.fetch_user(
                discord_id
            )
            if user:
                await user.send(
                    f"✅ Linked your Discord to osu! account '{osu_name}' "
                    f"(id {osu_id})."
                )
        except Exception as e:
            logger.warning(f"Failed to send DM to Discord ID {discord_id}: {e}")

        html = """
            <!doctype html>
            <html>
            <head><meta charset="utf-8"><title>osu! link</title></head>
            <body style="font-family: system-ui, sans-serif;">
                <h2>✅ Linked successfully</h2>
                <p>You can close this tab and return to Discord.</p>
            </body>
            </html>
            """
        return web.Response(text=html, content_type="text/html")