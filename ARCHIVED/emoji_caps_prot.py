from __future__ import annotations

import random
import re
from typing import List, Optional

import discord
import emojis
from cogs.mod.method import instant_action_parser
from core import Cog, Context, Parrot
from utilities.infraction import warn

with open("extra/duke_nekum.txt", encoding="utf-8", errors="ignore") as f:
    quotes = f.read().split("\n")


class EmojiCapsProt(Cog):
    def __init__(self, bot: Parrot):
        self.bot = bot
        self.__instant_action_parser = instant_action_parser
        self.ON_TESTING = False

    async def delete(self, message: discord.Message) -> None:
        await message.delete(delay=0)

    def get_emoji_count(self, message_content: str) -> int:
        str_count = emojis.count(message_content)
        dis_count = len(
            re.findall(
                r"<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>",
                message_content,
            )
        )
        return int(str_count + dis_count)

    def get_caps_count(self, message_content: str) -> int:
        return len(re.findall(r"[A-Z]", message_content))

    def is_caps_infilterated(self, message: discord.Message) -> Optional[bool]:
        
        if not (data_c := self.bot.guild_configurations_cache.get(message.guild.id)):
            return
        if not data_c["automod"]["caps"]["enable"]:
            return False
        ignore: List[int] = data_c["automod"]["caps"]["channel"]

        if message.channel.id in ignore:
            return False
        limit: Optional[int] = data_c["automod"]["caps"]["limit"]

        if limit and limit <= (self.get_caps_count(message.content)):
            return True

    def is_emoji_infilterated(self, message: discord.Message) -> Optional[bool]:
        if not (data_c := self.bot.guild_configurations_cache.get(message.guild.id)):
            return
        if not data_c["automod"]["emoji"]["enable"]:
            return False
        ignore: List[int] = data_c["automod"]["emoji"]["channel"]

        if message.channel.id in ignore:
            return False
        limit: Optional[int] = data_c["automod"]["emoji"]["limit"]

        if limit and limit <= (self.get_emoji_count(message.content)):
            return True

    async def _on_message_passive(self, message: discord.Message):
        # sourcery skip: low-code-quality
        if message.author.public_flags.verified_bot or not message.guild:
            return

        if isinstance(message.author, discord.User):
            return
        caps_: bool = self.is_caps_infilterated(message)
        emoj_: bool = self.is_emoji_infilterated(message)
        ctx: Context = await self.bot.get_context(message, cls=Context)
        data = self.bot.guild_configurations_cache[message.guild.id]
        if emoj_:
            to_delete: bool = data["automod"]["emoji"]["autowarn"]["to_delete"]

            if to_delete:
                await message.delete(delay=0)

            to_warn: bool = data["automod"]["emoji"]["autowarn"]["enable"]
            ignored_roles: List[int] = data["automod"]["emoji"]["autowarn"]["role"]

            if any(role.id in ignored_roles for role in message.author.roles):
                return
            instant_action: str = data["automod"]["emoji"]["autowarn"]["punish"]["type"]
            if instant_action and to_warn:
                await self.__instant_action_parser(
                    name=instant_action,
                    ctx=ctx,
                    message=message,
                    **data["automod"]["mention"]["autowarn"]["punish"],
                )

            if to_warn and not instant_action:
                await warn(
                    message.guild,
                    message.author,
                    "Automod: Mass Emoji",
                    moderator=self.bot.user,
                    message=message,
                    at=message.created_at,
                    ctx=ctx,
                )

                if mod_cog := self.bot.get_cog("Moderator"):
                    await mod_cog.warn_task(target=message.author, ctx=ctx)

            await message.channel.send(
                f"{message.author.mention} *{random.choice(quotes)}* **[Excess Emoji] {'[Warning]' if to_warn else ''}**",
                delete_after=10,
            )
        if caps_:
            to_delete: bool = data["automod"]["caps"]["autowarn"]["to_delete"]

            if to_delete:
                await message.delete(delay=0)
            to_warn = data["automod"]["caps"]["autowarn"]["enable"]
            ignored_roles: List[int] = data["automod"]["caps"]["autowarn"]["role"]

            if any(role.id in ignored_roles for role in message.author.roles):
                return

            instant_action: str = data["automod"]["caps"]["autowarn"]["punish"]["type"]
            if instant_action and to_warn:
                await self.__instant_action_parser(
                    name=instant_action,
                    ctx=ctx,
                    message=message,
                    **data["automod"]["mention"]["autowarn"]["punish"],
                )
                return

            if to_warn:
                await warn(
                    message.guild,
                    message.author,
                    "Automod: Excess Caps",
                    moderator=self.bot.user,
                    message=message,
                    at=message.created_at,
                    ctx=ctx,
                )

                await self.bot.get_cog("Moderator").warn_task(
                    target=message.author, ctx=ctx
                )

            await message.channel.send(
                f"{message.author.mention} *{random.choice(quotes)}* **[Excess Caps] {'[Warning]' if to_warn else ''}**",
                delete_after=10,
            )

    @Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self.bot.wait_until_ready()
        await self._on_message_passive(message)

    @Cog.listener()
    async def on_message_edit(
        self, before: discord.Message, after: discord.Message
    ) -> None:
        await self.bot.wait_until_ready()
        if before.content != after.content:
            await self._on_message_passive(after)