from __future__ import annotations

import time
from typing import Literal

import discord
from core import Cog, Context, Parrot
from discord import app_commands
from discord.ext import commands

from .modals import WhisperModal


class ContextMenu(Cog):
    def __init__(self, bot: Parrot) -> None:
        self.bot = bot
        self.ON_TESTING = False

        self.__interpret_as_command = app_commands.ContextMenu(
            name="Interpret as command",
            callback=self.ctx_menu_interpret_as_command,
        )
        self.__whisper_message = app_commands.ContextMenu(
            name="Whisper message",
            callback=self.ctx_menu_whisper,
        )

        self.bot.tree.add_command(self.__interpret_as_command)
        self.bot.tree.add_command(self.__whisper_message)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.__interpret_as_command.name)
        self.bot.tree.remove_command(self.__whisper_message.name)

    async def ctx_menu_interpret_as_command(self, interaction: discord.Interaction, message: discord.Message) -> None:
        # await interaction.response.defer(thinking=False)
        if message.guild is None:
            await interaction.response.send_message(
                f"{interaction.user.mention} interpreting as command is only available in guilds.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(f"{interaction.user.mention} processing...", ephemeral=True)
        prefix = await self.bot.get_guild_prefixes(message.guild)
        if message.content.startswith(prefix):
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} the command is already interpreted as command. Do you think it's an error? Please report it.",
            )
            return

        if message.author.bot:
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} the message is from a bot. Can't interpret it as command.",
            )
            return
        ini = time.perf_counter()

        message.content = f"{prefix}{message.content}"
        message.author = interaction.user
        await self.bot.process_commands(message)

        end = time.perf_counter()
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} completed command interpretation. It took {end - ini:.2f} seconds.",
        )

    async def ctx_menu_whisper(self, interaction: discord.Interaction, message: discord.Message) -> None:
        if message.guild is None:
            await interaction.response.send_message(
                f"{interaction.user.mention} whispering is only available in guilds.",
                ephemeral=True,
            )
            return

        if message.author.bot:
            await interaction.response.send_message(
                f"{interaction.user.mention} the message is from a bot. Can't whisper message.",
            )
            return

        await interaction.response.send_modal(WhisperModal(message))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(
        self,
        ctx: Context,
        guilds: commands.Greedy[discord.Object],
        spec: Literal["~", "*"] | None = None,
    ) -> None:
        if not guilds:
            if spec == "~":
                fmt = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                fmt = await ctx.bot.tree.sync(guild=ctx.guild)
            else:
                fmt = await ctx.bot.tree.sync()

            await ctx.send(
                f"{ctx.author.mention} \N{SATELLITE ANTENNA} Synced {len(fmt)} commands {'globally' if spec is None else 'to the current guild.'}",
            )

        else:
            fmt = 0
            for guild in guilds:
                try:
                    await ctx.bot.tree.sync(guild=guild)
                except discord.HTTPException:
                    pass
                else:
                    fmt += 1

            await ctx.send(f"{ctx.author.mention} \N{SATELLITE ANTENNA} Synced the tree to {fmt}/{len(guilds)} guilds.")

        await self.bot.update_app_commands_cache()


async def setup(bot: Parrot) -> None:
    await bot.add_cog(ContextMenu(bot))
