from __future__ import annotations

import re
import discord

from ...ext.emoji_convert import convert_emoji
from ...ext.html_generator import (
    PARSE_MODE_NONE,
    custom_emoji,
    emoji,
    fill_out,
)


class Reaction:
    def __init__(self, reaction: discord.Reaction, guild: discord.Guild):
        self.reaction = reaction
        self.guild = guild

    async def flow(self):
        await self.build_reaction()

        return self.reaction

    async def build_reaction(self):
        if ":" in str(self.reaction.emoji):
            emoji_animated = re.compile(r"&lt;a:.*:.*&gt;")
            if emoji_animated.search(str(self.reaction.emoji)):
                await self.create_discord_reaction("gif")
            else:
                await self.create_discord_reaction("png")
        else:
            await self.create_standard_emoji()

    async def create_discord_reaction(self, emoji_type):
        pattern = ":.*:(\d*)"
        emoji_id = re.search(pattern, str(self.reaction.emoji))[1]
        self.reaction = await fill_out(
            self.guild,
            custom_emoji,
            [
                ("EMOJI", str(emoji_id), PARSE_MODE_NONE),
                ("EMOJI_COUNT", str(self.reaction.count), PARSE_MODE_NONE),
                ("EMOJI_FILE", emoji_type, PARSE_MODE_NONE),
            ],
        )

    async def create_standard_emoji(self):
        react_emoji = await convert_emoji(self.reaction.emoji)
        self.reaction = await fill_out(
            self.guild,
            emoji,
            [
                ("EMOJI", str(react_emoji), PARSE_MODE_NONE),
                ("EMOJI_COUNT", str(self.reaction.count), PARSE_MODE_NONE),
            ],
        )
