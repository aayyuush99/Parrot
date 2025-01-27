from __future__ import annotations

import time

import wavelink

import discord
from core import Context, Parrot
from discord.ext import commands


class ModalInput(discord.ui.Modal, title="Name of Song"):
    name: discord.ui.TextInput = discord.ui.TextInput(
        label="Name",
        placeholder="Ex. Ice Cream - Blackpink",
        required=True,
        max_length=300,
    )

    def __init__(self, player: wavelink.Player, *, ctx: Context) -> None:
        super().__init__()
        self.player = player
        self.ctx = ctx

        self.bot = self.ctx.bot

    async def on_submit(self, interaction: discord.Interaction) -> None:
        cmd: commands.Command = self.bot.get_command("play")
        await interaction.response.send_message(f"Recieved `{self.name.value}`", ephemeral=True)

        try:
            await self.ctx.invoke(cmd, search=self.name.value)
        except commands.CommandError as e:
            return await interaction.response.edit_message(content=f"Error while invoking `play` command: {str(e)}")

        await interaction.response.edit_message(
            content="Invoked `play` command",
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:  # type: ignore
        if interaction.response.is_done():
            await interaction.response.edit_message(content="Oops! Something went wrong.")


class MusicView(discord.ui.View):
    message: discord.Message | None

    def __init__(self, vc: discord.VoiceChannel, *, timeout: float | None = None, ctx: Context) -> None:
        super().__init__(timeout=timeout or 300)
        self.vc = vc
        self.ctx = ctx

        self.bot: Parrot = self.ctx.bot
        self.player: wavelink.Player = self.ctx.voice_client

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in [i.id for i in self.vc.members]:
            await interaction.response.send_message(
                "You must be in the bot's voice channel to use this command.",
                ephemeral=True,
            )
            return False
        return True

    async def __add_to_playlist(self, user: discord.User | discord.Member):
        await self.bot.user_collections_ind.update_one(
            {"_id": user.id},
            {
                "$addToSet": {
                    "playlist": {
                        "id": self.player.current.identifier,
                        "song_name": getattr(self.player.current, "title", None),
                        "url": getattr(self.player.current, "uri", None),
                    },
                },
            },
            upsert=True,
        )

    async def __remove_from_playlist(self, user: discord.User | discord.Member):
        await self.bot.user_collections_ind.update_one(
            {"_id": user.id},
            {
                "$pull": {
                    "playlist": {
                        "id": self.player.current.identifier,
                        "song_name": self.player.current.title,
                        "url": self.player.current.uri,
                    },
                },
            },
            upsert=True,
        )

    async def __send_interal_error_response(self, interaction: discord.Interaction) -> None:
        self.disable_all()
        await interaction.followup.send(
            "Running `loop` command from the context failed. Possible reasons:\n"
            "- The bot is not in a voice channel.\n"
            "- The bot is not in the same voice channel as you.\n"
            "- The bot is not playing music.\n"
            "- You are missing DJ role or Manage Channels permission.\n",
            ephemeral=True,
        )
        await self.on_timeout()

    @discord.ui.button(
        custom_id="LOOP",
        emoji="\N{CLOCKWISE RIGHTWARDS AND LEFTWARDS OPEN CIRCLE ARROWS}",
    )
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        cmd: commands.Command = self.bot.get_command("loop")
        try:
            await self.ctx.invoke(cmd)
        except commands.CommandError:
            return await self.__send_interal_error_response(interaction)
        await interaction.response.send_message("Invoked `loop` command.", ephemeral=True)

    @discord.ui.button(
        custom_id="LOOP_CURRENT",
        emoji="\N{CLOCKWISE RIGHTWARDS AND LEFTWARDS OPEN CIRCLE ARROWS WITH CIRCLED ONE OVERLAY}",
    )
    async def loop_current(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        cmd: commands.Command = self.bot.get_command("loop")
        try:
            await self.ctx.invoke(cmd, "current")
        except commands.CommandError:
            return await self.__send_interal_error_response(interaction)
        await interaction.response.send_message("Invoked `loop current` command.", ephemeral=True)

    @discord.ui.button(custom_id="SHUFFLE", emoji="\N{TWISTED RIGHTWARDS ARROWS}")
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.queue.is_empty:
            return await interaction.response.send_message("There is no music to shuffle.", ephemeral=True)

        await interaction.response.defer()
        cmd: commands.Command = self.bot.get_command("shuffle")
        try:
            await self.ctx.invoke(cmd)
        except commands.CommandError:
            return await self.__send_interal_error_response(interaction)
        await interaction.response.send_message("Invoked `shuffle` command.", ephemeral=True)

    @discord.ui.button(emoji="\N{THUMBS UP SIGN}", disabled=True)
    async def __like(self, interaction: discord.Interaction, button: discord.ui.Button):
        ...

    @discord.ui.button(emoji="\N{THUMBS DOWN SIGN}", disabled=True)
    async def __dislike(self, interaction: discord.Interaction, button: discord.ui.Button):
        ...

    @discord.ui.button(
        custom_id="PAUSE",
        emoji="\N{DOUBLE VERTICAL BAR}",
        row=1,
    )
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.is_playing():
            await interaction.response.defer()
            cmd: commands.Command = self.bot.get_command("pause")
            try:
                await self.ctx.invoke(cmd)
            except commands.CommandError:
                return await self.__send_interal_error_response(interaction)
            await interaction.response.send_message("Invoked `pause` command.", ephemeral=True)
            return
        await interaction.response.send_message("There is no music to pause.", ephemeral=True)

    @discord.ui.button(custom_id="PLAY", emoji="\N{BLACK RIGHT-POINTING TRIANGLE}", row=1)
    async def play(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.is_paused():
            await interaction.response.defer()
            cmd: commands.Command = self.bot.get_command("resume")
            try:
                await self.ctx.invoke(cmd)
            except commands.CommandError:
                return await self.__send_interal_error_response(interaction)
            await interaction.response.send_message("Invoked `resume` command.", ephemeral=True)
            return

        await interaction.response.send_modal(ModalInput(self.player, ctx=self.ctx))

    @discord.ui.button(custom_id="STOP", emoji="\N{BLACK SQUARE FOR STOP}", row=1)
    async def _stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Invoking `stop` command.", ephemeral=True)
        cmd: commands.Command = self.bot.get_command("stop")
        ini = time.perf_counter()
        try:
            await self.ctx.invoke(cmd)
        except commands.CommandError:
            return await self.__send_interal_error_response(interaction)

        await interaction.response.edit_message(
            f"Invoked `stop` command. Time: {round(time.perf_counter() - ini, 2)} seconds",
            ephemeral=True,
        )
        await self.on_timeout()

    @discord.ui.button(
        custom_id="SKIP",
        emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}",
        row=1,
    )
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Invoking `skip` command.", ephemeral=True)
        if self.player.queue.is_empty:
            return await interaction.response.send_message("There is no music to skip.", ephemeral=True)
        cmd: commands.Command = self.bot.get_command("skip")
        time.perf_counter()
        try:
            await self.ctx.invoke(cmd)
            await interaction.response.edit_message(
                "Invoked `skip` command. Time: {round(time.perf_counter() - ini, 2)} seconds",
                ephemeral=True,
            )
            await self.on_timeout()
        except commands.CommandError:
            return await self.__send_interal_error_response(interaction)

    @discord.ui.button(custom_id="LOVE", emoji="\N{HEAVY BLACK HEART}", row=1)
    async def love(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Added song to loved songs (Playlist).", ephemeral=True)
        await self.__add_to_playlist(interaction.user)

    def disable_all(self) -> None:
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True

    async def on_timeout(self) -> None:
        self.disable_all()
        if hasattr(self, "message"):
            await self.message.edit(view=self)  # type: ignore
