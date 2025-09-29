"""
Cog for osu! account linking commands.
"""
import logging
from typing import Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

from utils.database import get_link, delete_link
from utils.helpers import profile_card

logger = logging.getLogger(__name__)


class LinkView(ui.View):
    """
    View for the link command buttons.
    """
    def __init__(self, bot, user_id: int, oauth_url: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id

        # Add link button (direct to OAuth)
        authorise_btn = ui.Button(
            label="Authorise with osu!",
            style=discord.ButtonStyle.link,
            url=oauth_url
        )
        self.add_item(authorise_btn)

        # Add cancel button
        cancel_btn = ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.danger,
        )
        self.add_item(cancel_btn)
        cancel_btn.callback = self.cancel_callback

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        Ensure only the original user can interact with the view.
        """
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot interact with this button.", ephemeral=True)
            return False
        return True

    async def cancel_callback(self, interaction: discord.Interaction) -> None:
        """
        Cancel button callback: Acknowledge cancellation.
        """
        embed = discord.Embed(
            title="Link cancelled",
            description="Run `/link` to start again.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class UnlinkView(ui.View):
    """
    View for the unlink command confirmation buttons.
    """
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        Ensure only the original user can interact with the view.
        """
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot interact with this button.", ephemeral=True)
            return False
        return True

    @ui.button(label="Yes unlink my account", style=discord.ButtonStyle.success)
    async def confirm_unlink(self, interaction: discord.Interaction, button: ui.Button):
        """
        Confirm unlink button callback: Delete the link and confirm.
        """
        try:
            deleted = await delete_link(self.user_id)
            if deleted:
                embed = discord.Embed(
                    title="Account Unlinked",
                    description="Your osu! account has been unlinked successfully.",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                logger.info(f"Unlinked osu! account for user {self.user_id}")
            else:
                embed = discord.Embed(
                    title="No Link Found",
                    description="No osu! account was linked to unlink.",
                    color=discord.Color.orange()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                logger.warning(f"Attempted to unlink non-existent link for {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to unlink for {self.user_id}: {e}")
            embed = discord.Embed(
                title="Error",
                description="Failed to unlink your account.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)

    @ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_unlink(self, interaction: discord.Interaction, button: ui.Button):
        """
        Cancel unlink button callback: Acknowledge cancellation.
        """
        embed = discord.Embed(
            title="Unlink Cancelled",
            description="Your osu! account remains linked.",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class LinkCog(commands.Cog):
    """
    Cog containing commands for linking, unlinking, and querying osu! accounts.
    """
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="link", description="Link your Discord account to an osu! account.")
    async def link(self, interaction: discord.Interaction):
        """
        Link command: Send ephemeral view with authorisation buttons.
        """
        # Check if already linked
        existing = await get_link(interaction.user.id)
        if existing:
            osu_username = existing[1]
            embed = discord.Embed(
                title="Already Linked",
                description=f"You already have osu! account '{osu_username}' linked.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Generate OAuth URL
        try:
            oauth_url = await self.bot.oauth.authorize_url_for(interaction.user.id)
        except Exception as e:
            logger.error(f"Failed to generate OAuth URL for {interaction.user.id}: {e}")
            embed = discord.Embed(
                title="Error",
                description="Failed to generate authorisation link.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        view = LinkView(self.bot, interaction.user.id, oauth_url)
        embed = discord.Embed(
            title="Link osu! Account",
            description="Click the button below to authorise with osu!",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        logger.info(f"Link command invoked by {interaction.user.id}")

    @app_commands.command(name="unlink", description="Unlink your osu! account from Discord.")
    async def unlink(self, interaction: discord.Interaction):
        """
        Unlink command: Check link and send confirmation view if exists.
        """
        existing = await get_link(interaction.user.id)
        if not existing:
            embed = discord.Embed(
                title="No Link",
                description="You do not have a linked osu! account.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        osu_username = existing[1]
        embed = discord.Embed(
            title="Unlink osu! Account",
            description=f"Are you sure you want to disconnect osu!bot from your osu! account: **{osu_username}**?",
            color=discord.Color.orange()
        )
        view = UnlinkView(self.bot, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        logger.info(f"Unlink command invoked by {interaction.user.id}")

    @app_commands.command(name="whois", description="Check a user's linked osu! profile.")
    @app_commands.describe(user="The Discord user to check.")
    @app_commands.guild_only()
    async def whois(self, interaction: discord.Interaction, user: discord.Member):
        """
        Whois command: Show linked osu! profile for a server member.
        """
        existing = await get_link(user.id)
        if existing:
            osu_user_id, osu_username, _ = existing
            embed = discord.Embed(
                title=f"{user.display_name}'s osu! Profile",
                description=f"**{osu_username}**\n[View Profile](https://osu.ppy.sh/users/{osu_user_id})",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title=f"{user.display_name}'s osu! Profile",
                description="That user does not have a linked osu! profile.",
                color=discord.Color.red()
            )

        # await interaction.response.send_message(embed=embed, ephemeral=True)
        user_data = self.bot.osu_client.get_user(identifier = user.id)
        embed = profile_card(user_data)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"Whois command invoked by {interaction.user.id} for {user.id}")


async def setup(bot):
    """
    Setup function to add the cog to the bot.
    """
    await bot.add_cog(LinkCog(bot))
    logger.info("Loaded link cog.")