from __future__ import annotations

import asyncio
import io
import itertools
import os
import random
import re
import unicodedata
from contextlib import suppress
from datetime import datetime
from time import time
from typing import TYPE_CHECKING

import discord
from core import Cog
from discord.ext import commands, tasks
from utilities.checks import in_support_server

try:
    import topgg  # noqa: F401 # pylint: disable=import-error

    HAS_TOP_GG = True
except ImportError:
    HAS_TOP_GG = False


from core import Context, Parrot

if TYPE_CHECKING:
    from pymongo.collection import Collection

    if HAS_TOP_GG:
        from topgg.types import BotVoteData

    from cogs.api import Gist

from tabulate import tabulate

from utilities.config import SUPPORT_SERVER_ID

EMOJI = "\N{WASTEBASKET}"
MESSAGE_ID = 1025455601398075535
VOTER_ROLE_ID = 836492413312040990
QU_ROLE = 851837681688248351
MEMBER_ROLE_ID = 1022216700650868916
GENERAL_CHAT = 1022211381031866459
RAINBOW_ROLE = 1121978468389896235
GENERAL_VOICE = 1022337864379404478
SERVER_MOD = 1022231265409241088
CORE_MAINTAINER_ROLE = 1022216515598164019

__all__ = ("Sector1729",)


with open("extra/adjectives.txt", encoding="utf-8", errors="ignore") as f:
    ADJECTIVES = f.read().splitlines()

with open("extra/mr_robot.txt", encoding="utf-8", errors="ignore") as f:
    MR_ROBOT = f.read().splitlines()


class Sector1729(Cog):
    def __init__(self, bot: Parrot) -> None:
        self.bot = bot
        self._cache: dict[int, int | float] = {}
        self.vote_reseter.start()
        self.ON_TESTING = False

        self.lock: asyncio.Lock = asyncio.Lock()
        self.__assignable_roles: list[int] = [
            1022896161167777835,  # NSFW ACCESS
            1022896162107310130,  # BOT ACCESS
            1022897174624866426,  # MUSIC ACCESS
        ]
        self.adjectives = ADJECTIVES
        self.mr_robots = MR_ROBOT

        self._updating_channel = True
        self._updating_rainbow = True

        self.iter_cycle = itertools.cycle(self.mr_robots)
        self.change_rainbow_role.start()
        self.change_channel_name.start()

        self._is_locked = True
        self.__locked_channels = set()

    async def cog_check(self, ctx: Context) -> bool:
        return ctx.guild is not None and ctx.guild.id == getattr(ctx.bot.server, "id", SUPPORT_SERVER_ID)

    async def cog_unload(self) -> None:
        if self.change_channel_name.is_running():
            self.change_channel_name.cancel()

        if self.change_rainbow_role.is_running():
            self.change_rainbow_role.cancel()

        if self.vote_reseter.is_running():
            self.vote_reseter.cancel()

    @Cog.listener("on_raw_reaction_add")
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if (
            payload.message_id != MESSAGE_ID
            or str(payload.emoji) != EMOJI
            and unicodedata.name(str(payload.emoji)) != "WASTEBASKET"
        ):
            return
        user_id: int = payload.user_id
        user: discord.User | None = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, user_id)

        channel: discord.TextChannel | None = self.bot.get_channel(payload.channel_id)  # type: ignore

        if channel is None:
            return

        msg: discord.Message | None = await self.bot.get_or_fetch_message(channel, MESSAGE_ID)

        async def __remove_reaction(msg: discord.Message) -> None:
            for reaction in msg.reactions:
                if user:
                    try:
                        await msg.remove_reaction(reaction.emoji, user)
                    except discord.HTTPException:
                        pass
                    return

        if then := self._cache.get(payload.user_id):
            if abs(time() - then) < 60:
                await channel.send(
                    f"<@{payload.user_id}> You can only use the emoji once every minute.",
                    delete_after=7,
                )
                if msg:
                    await __remove_reaction(msg)
                    return

        self._cache[payload.user_id] = time() + 60

        _msg: discord.Message = await channel.send(f"<@{payload.user_id}> deleting messages - 0/50")

        if user is None or user.bot:
            return

        dm: discord.DMChannel = await user.create_dm()

        i = 1
        async for msg in dm.history(limit=50):
            if msg.author.id == self.bot.user.id:
                await msg.delete()
            i += 1
            if i % 10 == 0:
                await _msg.edit(content=f"<@{payload.user_id}> deleting messages - {i}/50")

        if msg:
            await __remove_reaction(msg)
        await _msg.edit(
            content=f"<@{payload.user_id}> deleting messages - 50/50! Done!",
            delete_after=2,
        )

    @Cog.listener("on_dbl_vote")
    async def on_dbl_vote(self, data: BotVoteData):
        assert self.bot.server is not None
        member: discord.Member | discord.User | None = await self.bot.get_or_fetch_member(
            self.bot.server,
            data.user,
        )

        if member is None and not isinstance(member, discord.Member):
            return

        await member.add_roles(discord.Object(id=VOTER_ROLE_ID), reason="Voted for the bot on Top.gg")
        await self.__add_to_db(member)

    @Cog.listener("on_member_join")
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != SUPPORT_SERVER_ID:
            return

        await member.add_roles(discord.Object(id=MEMBER_ROLE_ID), reason="Member role add")
        if await self.bot.topgg.get_user_vote(member.id):
            await member.add_roles(discord.Object(id=VOTER_ROLE_ID), reason="Voted for the bot on Top.gg")

    @commands.command(name="claimvote", hidden=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    @in_support_server()
    async def claim_vote(self, ctx: Context):
        assert isinstance(ctx.author, discord.Member)
        if ctx.author._roles.has(VOTER_ROLE_ID):
            return await ctx.error("You already have the vote role.")

        if await self.bot.user_collections_ind.find_one(
            {"_id": ctx.author.id, "topgg_vote_expires": {"$gte": time()}},
        ) or await self.bot.topgg.get_user_vote(ctx.author.id):
            role = discord.Object(id=VOTER_ROLE_ID)
            await ctx.author.add_roles(role, reason="Voted for the bot on Top.gg")
            await ctx.send("You have claimed your vote for the bot on Top.gg. Added Golden Role.")
            return

        await ctx.send(
            "Seems you haven't voted for the bot on Top.gg Yet. This might be error. "
            f"Consider asking the owner of the bot ({self.bot.author_obj})",
        )

    @commands.command(name="myvotes", hidden=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    @in_support_server()
    async def my_votes(self, ctx: Context):
        if data := await self.bot.mongo.user_misc.find_one({"_id": ctx.author.id, "topgg_votes": {"$exists": True}}):
            await ctx.send(f"You voted for **{self.bot.user}** for **{len(data['topgg_votes'])}** times on Top.gg")
        else:
            await ctx.send("You haven't voted for the bot on Top.gg yet.")

    async def __add_to_db(self, member: discord.Member) -> None:
        col: Collection = self.bot.user_collections_ind
        now = time()
        await col.update_one(
            {"_id": member.id},
            {
                "$set": {
                    "topgg_vote_time": now,
                    "topgg_vote_expires": now + 43200,
                },
                "$inc": {"topgg_votes": 1},
            },
            upsert=True,
        )  # type: ignore

    @tasks.loop(minutes=5)
    async def vote_reseter(self):
        async with self.lock:
            col: Collection = self.bot.user_collections_ind
            now_plus_12_hours = time() + 43200

            async for doc in col.find({"topgg_vote_expires": {"$lte": now_plus_12_hours}}):  # type: ignore
                guild = self.bot.server
                role = discord.Object(id=VOTER_ROLE_ID)

                await col.update_one({"_id": doc["_id"]}, {"$set": {"topgg_vote_expires": 0}})  # type: ignore
                if guild and (member := guild.get_member(doc["_id"])):
                    await member.remove_roles(role, reason="Top.gg vote expired")

    @tasks.loop(minutes=30)
    async def change_channel_name(self):
        if not self._updating_channel:
            return

        if self._is_locked:
            return

        try:
            await self.bot.wait_for("on_bot_idle", timeout=300)
        except asyncio.TimeoutError:
            await self.bot.wait_until_ready()

        general_chat: discord.TextChannel = self.bot.get_channel(GENERAL_CHAT)  # type: ignore
        if general_chat is not None:
            LINE = "\N{BOX DRAWINGS LIGHT VERTICAL}"
            EMOJI = "\N{SPEECH BALLOON}"
            await general_chat.edit(
                name=f"{LINE}{EMOJI}{LINE}{random.choice(self.adjectives)}-general",
                reason="General chat name update",
            )

        general_voice: discord.VoiceChannel = self.bot.get_channel(GENERAL_VOICE)  # type: ignore
        if general_voice is not None:
            await general_voice.edit(
                name=f"{next(self.iter_cycle)}",
                reason="General voice name update",
            )

    @tasks.loop(minutes=10)
    async def change_rainbow_role(self):
        if not self._updating_rainbow:
            return

        if self._is_locked:
            return

        try:
            await self.bot.wait_for("on_bot_idle", timeout=300)
        except asyncio.TimeoutError:
            await self.bot.wait_until_ready()

        role: discord.Role = self.bot.server.get_role(RAINBOW_ROLE)  # type: ignore
        if role is not None:
            try:
                await role.edit(
                    colour=discord.Colour.random(),
                    reason="Rainbow role update",
                )
            except discord.HTTPException:
                pass

    @vote_reseter.before_loop
    async def before_vote_reseter(self):
        await self.bot.wait_until_ready()

    @Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self.bot.wait_until_ready()
        if message.guild is None or message.guild.id != SUPPORT_SERVER_ID:
            return

        created: datetime | None = getattr(message.author, "created_at", None)
        joined: datetime | None = getattr(message.author, "joined_at", None)

        if not (joined and created):
            return

        seconds = (created - joined).total_seconds()
        if seconds >= 86400 and isinstance(message.author, discord.Member) and message.author._roles.has(QU_ROLE):
            with suppress(discord.HTTPException):
                await message.author.remove_roles(
                    discord.Object(id=QU_ROLE),
                    reason="Account age crosses 1d",
                )

    @Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        await self.bot.wait_until_ready()
        if message.guild is None or message.guild.id != SUPPORT_SERVER_ID:
            return

        if not hasattr(self, "message_delete_webhook"):
            message_delete: discord.TextChannel = discord.utils.get(message.guild.text_channels, name="message-delete")  # type: ignore
            if message_delete is None:
                return

            webhooks = await message_delete.webhooks()
            webhook = webhooks[0]
            self.message_delete_webhook = webhook

        if message.author.bot:
            return

        embed = (
            discord.Embed(
                title="Message Deleted",
                description=message.content,
            )
            .set_author(
                name=f"{message.author} ({message.author.id})",
                icon_url=message.author.display_avatar.url,
            )
            .add_field(
                name="Channel",
                value=f"{message.channel.mention} ({message.channel.id})",
                inline=False,
            )
            .set_thumbnail(
                url=message.guild.icon.url,
            )
        )

        if message.attachments:
            embed.add_field(
                name="Attachments",
                value="\n".join(attachment.proxy_url for attachment in message.attachments),
                inline=False,
            )

        await self.bot._execute_webhook(webhook=self.message_delete_webhook, embed=embed)

    @commands.group(name="sector", aliases=["sector1729", "sector17"], invoke_without_command=True)
    async def sector_17_29(self, ctx: Context):
        """Commands related to SECTOR 17-29."""
        if not ctx.invoked_subcommand:
            await ctx.bot.invoke_help_command(ctx)

    @sector_17_29.command(name="info", aliases=["about"])
    @in_support_server()
    async def sector_17_29_about(self, ctx: Context):
        """Information about the SECTOR 17-29."""
        description = (
            f"SECTOR 17-29 is support server of the bot (Parrot) and formely a "
            f"community server for the stream Beasty Stats.\n"
            f"[Click here]({self.bot.support_server}) to join the server"
        )
        await ctx.send(embed=discord.Embed(description=description))

    @sector_17_29.command(name="color")
    @in_support_server()
    async def sector_17_29_color(self, ctx: Context, *, color: str | None = None):
        """Assign yourself color role."""
        if not color:
            return

        assert isinstance(ctx.author, discord.Member) and ctx.bot.server is not None

        role = discord.utils.get(ctx.bot.server.roles, name=f"[SELF] - COLOR {color.upper()}")
        if role is None:
            await ctx.error(f"{ctx.author.mention} no color named {color}!")
            return

        if ctx.author._roles.has(role.id):
            return await ctx.wrong()

        await ctx.author.add_roles(role, reason="Color role added")
        await ctx.tick()

    @sector_17_29.command(name="uncolor")
    @in_support_server()
    async def sector_17_29_uncolor(self, ctx: Context, *, color: str | None = None):
        """Unassign yourself color role."""
        if not color:
            return

        assert isinstance(ctx.author, discord.Member) and ctx.bot.server is not None

        role = discord.utils.get(ctx.bot.server.roles, name=f"[SELF] - COLOR {color.upper()}")
        if role is None:
            await ctx.error(f"{ctx.author.mention} no color named {color}!")
            return

        if ctx.author._roles.has(role.id):
            await ctx.author.remove_roles(role, reason="Color role removed")
            await ctx.tick()
            return

        await ctx.wrong()

    @sector_17_29.command(name="role")
    @in_support_server()
    async def sector_17_29_role(self, ctx: Context, *, role: discord.Role | None):
        """Assign yourself role."""
        if not role:
            await ctx.error(f"{ctx.author.mention} that role do not exists")
            return

        assert isinstance(ctx.author, discord.Member) and ctx.bot.server is not None

        if not role.name.startswith("[SELF]"):
            await ctx.error(f"{ctx.author.roles} you don't have permission to assign yourself that role")
            return

        if ctx.author._roles.has(role.id):
            await ctx.error(f"{ctx.author.mention} you already have that role")
            return

        await ctx.author.add_roles(role, reason="Self role - Role")
        await ctx.tick()

    @sector_17_29.command(name="unrole")
    @in_support_server()
    async def sector_17_29_unrole(self, ctx: Context, *, role: discord.Role | None):
        """Unassign yourself role."""
        if not role:
            await ctx.error(f"{ctx.author.mention} that role do not exists")
            return

        assert isinstance(ctx.author, discord.Member) and ctx.bot.server is not None

        if role.id not in self.__assignable_roles:
            await ctx.error(f"{ctx.author.mention} you don't have permission to unassign yourself that role")
            return

        if not ctx.author._roles.has(role.id):
            await ctx.error(f"{ctx.author.mention} you do not have that role")
            return

        await ctx.author.remove_roles(role, reason="Self role - Unrole")
        await ctx.tick()

    @Cog.listener("on_message")
    async def extra_parser_on_message(self, message: discord.Message) -> None:
        await self.bot.wait_until_ready()
        if message.guild is not None and self.bot.server and message.guild.id != self.bot.server.id:
            return

        await self.nickname_parser(message)

        if self.bot.owner_ids and message.author.id not in self.bot.owner_ids:
            ls = message.content.split("\n")
            inside_code_block = False
            for line in ls:
                if line.startswith("```"):
                    inside_code_block = not inside_code_block
                if line.startswith("# ") and not inside_code_block:  # dont let user use markdown syntax
                    await message.delete(delay=0)

    async def nickname_parser(self, message: discord.Message) -> None:
        regex = re.compile(r"^[a-zA-Z0-9_ \[\]\(\)]+$")

        ctx: Context[Parrot] = await self.bot.get_context(message, cls=Context)

        if not isinstance(ctx.author, discord.Member):
            return

        if not regex.match(ctx.author.display_name) and ctx.guild:
            try:
                await ctx.author.edit(nick="Moderated Nickname", reason="Nickname moderated")
                await ctx.author.send(
                    f"Your nickname in {ctx.guild.name} has been moderated because it contained invalid characters, you can still change your nickname.",
                    view=ctx.send_view(),
                )
            except discord.HTTPException:
                pass

    @sector_17_29.group(name="add")
    async def sector_17_29_add(self, ctx: Context):
        """Add something to the server."""
        if not ctx.invoked_subcommand:
            await ctx.bot.invoke_help_command(ctx)

    @sector_17_29.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock_sector_17_29(self, ctx: Context, *, reason: str | None = None):
        """Lock updating general chat and railway role. And all messagable channels."""
        self._is_locked = True

        if reason is not None:
            for channel in ctx.guild.channels:
                if (
                    isinstance(channel, discord.abc.Messageable)
                    and channel.permissions_for(ctx.guild.default_role).send_messages
                ):
                    await channel.set_permissions(ctx.guild.default_role, send_messages=False, reason=reason)
                    await channel.send(f"Server On Lockdown: {reason}")
                    self.__locked_channels.add(channel.id)

                if (
                    isinstance(channel, discord.VoiceChannel | discord.StageChannel)
                    and channel.permissions_for(ctx.guild.default_role).connect
                ):
                    await channel.set_permissions(ctx.guild.default_role, connect=False, reason=reason)
                    self.__locked_channels.add(channel.id)

        await ctx.send("Locked")

    @sector_17_29.command(name="unlock", aliases=["release"])
    @commands.has_permissions(manage_channels=True)
    async def unlock_sector_17_29(self, ctx: Context, *, reason: str | None = None):
        """Unlock updating general chat and railway role. And unlock all messagable channels."""
        self._is_locked = False

        if reason is not None:
            for channel in ctx.guild.channels:
                if channel.id in self.__locked_channels:
                    if (
                        isinstance(channel, discord.abc.Messageable)
                        and not channel.permissions_for(ctx.guild.default_role).send_messages
                    ):
                        await channel.set_permissions(ctx.guild.default_role, send_messages=None, reason=reason)
                        await channel.send(f"Server Unlocked: {reason}")
                    if (
                        isinstance(channel, discord.VoiceChannel | discord.StageChannel)
                        and not channel.permissions_for(ctx.guild.default_role).connect
                    ):
                        await channel.set_permissions(ctx.guild.default_role, connect=None, reason=reason)
                    self.__locked_channels.remove(channel.id)

        await ctx.send("Unlocked")

    # Thanks
    #   - `aastha_ok`    (AASTHA#1206 - 925315596818718752)
    #   - `sourcandy_zz` (Sour Candy#8301 - 966599206880030760)
    @sector_17_29_add.command(name="adjective", aliases=["adj", "adjectives"])
    @commands.has_any_role(SERVER_MOD, CORE_MAINTAINER_ROLE)
    @commands.cooldown(1, 300, commands.BucketType.guild)
    @in_support_server()
    async def sector_17_29_add_adj(self, ctx: Context, *adjs: str):
        """Add adjective to the server."""
        if not adjs:
            return await ctx.bot.invoke_help_command(ctx)

        for adj in adjs:
            if len(adj) > 20:
                return await ctx.error(f"Adjective: {adj} is too long")

        for adj in adjs:
            if adj in self.adjectives:
                return await ctx.error(f"Adjective: {adj} already exists")

        self.adjectives.extend(list(adjs))
        self.adjectives = list(set(self.adjectives))
        await ctx.tick()

        await ctx.reply(f"Adjective added, Total count: {len(self.adjectives)}")

        cog: Gist = self.bot.get_cog("Gist")  # type: ignore
        table = tabulate({"Adjectives": adjs}, headers="keys", tablefmt="github")
        author = tabulate(
            {"Author": [f"{ctx.author}"], "ID": [ctx.author.id], "Is Mod?": ["Yes"]},
            headers="keys",
            tablefmt="github",
        )
        message = tabulate(
            {
                "Message": [f"`{ctx.message.clean_content}`"],
                "ID": [ctx.message.id],
                "Channel": [f"#{ctx.channel.name}"],  # type: ignore
                "Channel ID": [ctx.channel.id],
                "Guild": [f"{ctx.guild}"],
            },
            headers="keys",
            tablefmt="github",
        )
        if cog is not None:
            body = f"""## Add Adjectives

{table}

**In file: [`/extra/adjectives.txt`](https://github.com/rtk-rnjn/Parrot/blob/main/extra/adjectives.txt)**

---

### Author

{author}

---

### Message

{message}
"""
            url = await cog.create_issue(title="[Bot] Add Adjective", body=body)
            await ctx.reply(f"Created issue: {url}")

    @sector_17_29.group(name="remove")
    async def sector_17_29_remove(self, ctx: Context):
        """Remove something from the server."""
        if not ctx.invoked_subcommand:
            await ctx.bot.invoke_help_command(ctx)

    @sector_17_29_remove.command(name="adjective", aliases=["adj", "adjectives"])
    @commands.has_any_role(SERVER_MOD, CORE_MAINTAINER_ROLE)
    @in_support_server()
    async def sector_17_29_remove_adj(self, ctx: Context, *adjs: str):
        """Remove adjective from the server."""
        if not adjs:
            return await ctx.bot.invoke_help_command(ctx)

        for adj in adjs:
            if adj not in self.adjectives:
                return await ctx.error("Adjective do not exists")

        for adj in adjs:
            try:
                self.adjectives.remove(adj)
            except ValueError:
                pass
        await ctx.tick()

        await ctx.reply(f"Adjective removed, Total count: {len(self.adjectives)}")

    @commands.command()
    async def removebg(self, ctx: Context, *, url: str):
        """To remove the background from image."""
        async with self.bot.http_session.get(url) as img:
            imgdata = io.BytesIO(await img.read())

        response = await self.bot.http_session.post(
            "https://api.remove.bg/v1.0/removebg",
            data={"size": "auto", "image_file": imgdata},
            headers={"X-Api-Key": f'{os.environ["REMOVE_BG"]}'},
        )
        img = io.BytesIO(await response.read())
        await ctx.send(file=discord.File(img, "nobg.png"))
