from __future__ import annotations

import datetime
import io
import itertools
import os
from collections import Counter
from time import time

import psutil
import pygit2

import discord
from core import Cog, Context, Parrot
from discord import __version__ as discord_version
from discord.ext import commands
from utilities.config import SUPPORT_SERVER, SUPPORT_SERVER_ID, VERSION


class Meta(Cog):
    """Commands for utilities related to Discord or the Bot itself."""

    def __init__(self, bot: Parrot) -> None:
        self.bot = bot
        self.ON_TESTING = False

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name="\N{WHITE QUESTION MARK ORNAMENT}")

    @commands.command(name="ping")
    @commands.cooldown(1, 5, commands.BucketType.member)
    @Context.with_type
    async def ping(self, ctx: Context):
        """Get the latency of bot."""
        start = time()
        message = await ctx.reply("Pinging...")
        db = await self.bot.db_latency()
        end = time()
        await message.edit(
            content=(
                f"Pong! latency: {self.bot.latency*1000:,.0f} ms. "
                f"Response time: {(end-start)*1000:,.0f} ms. Database: {db*1000:,.0f} ms."
            ),
        )

    @commands.command(aliases=["av"])
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    @Context.with_type
    async def avatar(self, ctx: Context, *, member: discord.Member = None):
        """Get the avatar of the user. Make sure you don't misuse."""
        member = member or ctx.author
        embed = discord.Embed(timestamp=discord.utils.utcnow())
        # embed.add_field(
        #     name=member.name, value=f"[Download]({member.display_avatar.url})"
        # )
        response = await self.bot.http_session.get(member.display_avatar.url, headers=self.bot.GLOBAL_HEADERS)
        buffer = io.BytesIO(await response.read())

        embed.set_image(url="attachment://avatar.gif")

        await ctx.reply(embed=embed, file=discord.File(buffer, "avatar.gif"))

    @commands.command(name="owner")
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    @Context.with_type
    async def owner(self, ctx: Context):
        """Core and sole maintainer of this bot."""
        from utilities.config import AUTHOR_DISCRIMINATOR, AUTHOR_NAME, SUPER_USER

        owner = self.bot.get_user(int(SUPER_USER))
        if not owner:
            return await ctx.reply("Owner not found, for some reason.")

        await ctx.reply(
            embed=discord.Embed(
                title="Owner Info",
                description=(
                    f"This bot is being hosted and created by `{owner}` (He/Him). "
                    f"Previously known as {AUTHOR_NAME}#{AUTHOR_DISCRIMINATOR}. "
                    f"He is actually a dumb bot developer. He do not know why he made this shit bot. But it's cool"
                ),
                timestamp=discord.utils.utcnow(),
                color=ctx.author.color,
                url=f"https://discord.com/users/{owner.id}",
            ),
        )

    @commands.command(aliases=["guildavatar", "serverlogo", "servericon"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    @Context.with_type
    async def guildicon(self, ctx: Context):
        """Get the freaking server icon."""
        if not ctx.guild.icon:
            return await ctx.reply(f"{ctx.author.mention} {ctx.guild.name} has no icon yet!")

        embed = discord.Embed(timestamp=discord.utils.utcnow())
        embed.set_image(url=ctx.guild.icon.url)

        await ctx.reply(embed=embed)

    @commands.command(name="serverinfo", aliases=["guildinfo", "si", "gi"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    @Context.with_type
    async def server_info(self, ctx: Context):
        """Get the basic stats about the server."""
        guild = ctx.guild
        embed: discord.Embed = discord.Embed(
            title=f"Server Info: {ctx.guild.name}",
            colour=ctx.guild.owner.colour if ctx.guild.owner else discord.Colour.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"ID: {ctx.guild.id}")
        statuses = [
            len(list(filter(lambda m: str(m.status) == "online", ctx.guild.members))),
            len(list(filter(lambda m: str(m.status) == "idle", ctx.guild.members))),
            len(list(filter(lambda m: str(m.status) == "dnd", ctx.guild.members))),
            len(list(filter(lambda m: str(m.status) == "offline", ctx.guild.members))),
        ]

        fields = [
            ("Owner", ctx.guild.owner, True),
            ("Region", "Deprecated", True),
            ("Created at", f"{discord.utils.format_dt(ctx.guild.created_at)}", True),
            (
                "Total Members",
                (
                    f"Members: {len(ctx.guild.members)}\n"
                    f"Humans: {len(list(filter(lambda m: not m.bot, ctx.guild.members)))}\n"
                    f"Bots: {len(list(filter(lambda m: m.bot, ctx.guild.members)))}"
                ),
                True,
            ),
            (
                "Total channels",
                (
                    f"Categories: {len(ctx.guild.categories)}\n"
                    f"Text: {len(ctx.guild.text_channels)}\n"
                    f"Voice:{len(ctx.guild.voice_channels)}"
                ),
                True,
            ),
            (
                "General",
                (
                    f"Roles: {len(ctx.guild.roles)}\n"
                    f"Emojis: {len(ctx.guild.emojis)}\n"
                    f"Boost Level: {ctx.guild.premium_tier}"
                ),
                True,
            ),
            (
                "Statuses",
                (
                    f":green_circle: {statuses[0]}\n"
                    f":yellow_circle: {statuses[1]}\n"
                    f":red_circle: {statuses[2]}\n"
                    f":black_circle: {statuses[3]} [Blame Discord]"
                ),
                True,
            ),
        ]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        features = set(ctx.guild.features)
        all_features = {
            "PARTNERED": "Partnered",
            "VERIFIED": "Verified",
            "DISCOVERABLE": "Server Discovery",
            "COMMUNITY": "Community Server",
            "FEATURABLE": "Featured",
            "WELCOME_SCREEN_ENABLED": "Welcome Screen",
            "INVITE_SPLASH": "Invite Splash",
            "VIP_REGIONS": "VIP Voice Servers",
            "VANITY_URL": "Vanity Invite",
            "COMMERCE": "Commerce",
            "LURKABLE": "Lurkable",
            "NEWS": "News Channels",
            "ANIMATED_ICON": "Animated Icon",
            "BANNER": "Banner",
        }

        if info := [f":ballot_box_with_check: {label}" for feature, label in all_features.items() if feature in features]:
            embed.add_field(name="Features", value="\n".join(info))

        if guild.premium_tier != 0:
            boosts = f"Level {guild.premium_tier}\n{guild.premium_subscription_count} boosts"
            last_boost = max(guild.members, key=lambda m: m.premium_since or guild.created_at)
            if last_boost.premium_since is not None:
                boosts = f"{boosts}\nLast Boost: {last_boost} ({discord.utils.format_dt(last_boost.premium_since, 'R')})"
            embed.add_field(name="Boosts", value=boosts, inline=True)
        else:
            embed.add_field(name="Boosts", value="Level 0", inline=True)

        emoji_stats = Counter()
        for emoji in guild.emojis:
            if emoji.animated:
                emoji_stats["animated"] += 1
                emoji_stats["animated_disabled"] += not emoji.available
            else:
                emoji_stats["regular"] += 1
                emoji_stats["disabled"] += not emoji.available

        fmt = (
            f'Regular: {emoji_stats["regular"]}/{guild.emoji_limit}\n'
            f'Animated: {emoji_stats["animated"]}/{guild.emoji_limit}\n'
        )
        if emoji_stats["disabled"] or emoji_stats["animated_disabled"]:
            fmt = f'{fmt}Disabled: {emoji_stats["disabled"]} regular, {emoji_stats["animated_disabled"]} animated\n'

        fmt = f"{fmt}Total Emoji: {len(guild.emojis)}/{guild.emoji_limit*2}"
        embed.add_field(name="Emoji", value=fmt, inline=True)

        if ctx.guild.me.guild_permissions.ban_members:
            embed.add_field(
                name="Banned Members",
                value=f"{len([_ async for _ in ctx.guild.bans(limit=1000)])}+",
                inline=True,
            )
        if ctx.guild.me.guild_permissions.manage_guild:
            embed.add_field(name="Invites", value=f"{len(await ctx.guild.invites())}", inline=True)

        if ctx.guild.banner:
            embed.set_image(url=ctx.guild.banner.url)

        await ctx.reply(embed=embed)

    def format_commit(self, commit):
        short, _, _ = commit.message.partition("\n")
        short_sha2 = commit.hex[:6]
        commit_tz = datetime.timezone(datetime.timedelta(minutes=commit.commit_time_offset))
        commit_time = datetime.datetime.fromtimestamp(commit.commit_time).astimezone(commit_tz)

        # [`hash`](url) message (offset)
        offset = discord.utils.format_dt(commit_time.astimezone(datetime.timezone.utc), "R")
        return f"[`{short_sha2}`](https://github.com/rtk-rnjn/Parrot/commit/{commit.hex}) {short} ({offset})"

    def format_commit_from_json(self, commit: dict):
        # sourcery skip: aware-datetime-for-utc
        commit_hex = commit["sha"]
        short_sha2 = commit_hex[:6]
        commit_time = datetime.datetime.strptime(commit["commit"]["committer"]["date"], "%Y-%m-%dT%H:%M:%SZ")
        utc_offset = datetime.datetime.now() - datetime.datetime.utcnow()  # type: datetime.timedelta
        commit_tz = datetime.timezone(datetime.timedelta(minutes=utc_offset.total_seconds() // 60))
        commit_time = commit_time.astimezone(commit_tz)

        # [`hash`](url) message (offset)
        offset = discord.utils.format_dt(commit_time.astimezone(datetime.timezone.utc), "R")
        return f"[`{short_sha2}`](https://github.com/rtk-rnjn/Parrot/commit/{commit_hex}) {commit['commit']['message']} ({offset})"

    def get_last_commits(self, count=3):
        # check if the `.git` directory exists
        if not os.path.isdir(".git"):
            return
        repo = pygit2.Repository(".git")
        commits = list(itertools.islice(repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL), count))
        return "\n".join(self.format_commit(c) for c in commits)

    async def get_last_commits_async(self, count: int = 3):
        repo = "rtk-rnjn/Parrot"
        url = f"https://api.github.com/repos/{repo}/commits"

        async with self.bot.http_session.get(url) as response:
            if response.status != 200:
                return "Failed to get commits"

            data = await response.json()

        return "\n".join(self.format_commit_from_json(c) for c in data[:count])

    @commands.command(name="stats", aliases=["about"])
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    @Context.with_type
    async def show_bot_stats(self, ctx: Context):
        """Get the bot stats."""
        revision = self.get_last_commits(3) or await self.get_last_commits_async(3)
        embed = discord.Embed(
            title="Official Bot Server Invite",
            colour=ctx.author.colour,
            timestamp=discord.utils.utcnow(),
            description="Latest Changes:\n" + revision,
            url=SUPPORT_SERVER,
        )
        support_guild = self.bot.get_guild(SUPPORT_SERVER_ID)
        owner: discord.Member = await self.bot.get_or_fetch_member(support_guild, self.bot.author_obj.id)  # type: ignore  i am owner
        embed.set_author(name=str(owner), icon_url=owner.display_avatar.url)

        # statistics
        total_members = 0
        total_unique = len(self.bot.users)

        text = 0
        voice = 0
        guilds = 0
        for guild in self.bot.guilds:
            guilds += 1
            if guild.unavailable:
                continue

            total_members += guild.member_count or 0
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text += 1
                elif isinstance(channel, discord.VoiceChannel | discord.StageChannel):
                    voice += 1

        embed.add_field(name="Members", value=f"{total_members} total\n{total_unique} unique")
        embed.add_field(name="Channels", value=f"{text + voice} total\n{text} text\n{voice} voice")
        process = psutil.Process()
        memory_usage = process.memory_full_info().uss / 1024**2
        cpu_usage = process.cpu_percent() / psutil.cpu_count()
        embed.add_field(name="Process", value=f"{memory_usage:.2f} MiB\n{cpu_usage:.2f}% CPU")

        version = discord_version
        embed.add_field(name="Guilds", value=guilds)
        embed.add_field(name="Bot Version", value=VERSION)
        embed.add_field(name="Uptime", value=discord.utils.format_dt(self.bot.uptime, "R"))
        embed.set_footer(
            text=f"Made with discord.py v{version}",
            icon_url="http://i.imgur.com/5BFecvA.png",
        )
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="userinfo", aliases=["memberinfo", "ui", "mi"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    @Context.with_type
    async def user_info(self, ctx: Context, *, member: discord.Member = None):
        """Get the basic stats about the user."""
        target = member or ctx.author
        roles = list(target.roles)
        embed = discord.Embed(
            title="User information",
            colour=target.colour,
            timestamp=discord.utils.utcnow(),
        )

        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"ID: {target.id}")
        fields = [
            ("Name", str(target), True),
            ("Created at", f"{discord.utils.format_dt(target.created_at)}", True),
            ("Status", f"{str(target.status).title()} [Blame Discord]", True),
            (
                "Activity",
                f"{str(target.activity.type).split('.')[-1].title() if target.activity else 'N/A'} {target.activity.name if target.activity else ''} [Blame Discord]",
                True,
            ),
            ("Joined at", f"{discord.utils.format_dt(target.joined_at)}" if target.joined_at else "N/A", True),
            ("Boosted", bool(target.premium_since), True),
            ("Bot?", target.bot, True),
            ("Nickname", target.display_name, True),
            (f"Top Role [{len(roles)}]", target.top_role.mention, True),
        ]
        perms = []
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        if target.guild_permissions.administrator:
            perms.append("Administrator")
        if (
            target.guild_permissions.kick_members
            and target.guild_permissions.ban_members
            and target.guild_permissions.manage_messages
        ):
            perms.append("Server Moderator")
        if target.guild_permissions.manage_guild:
            perms.append("Server Manager")
        if target.guild_permissions.manage_roles:
            perms.append("Role Manager")
        if target.guild_permissions.moderate_members:
            perms.append("Can Timeout Members")
        embed.description = f"Key perms: {', '.join(perms or ['N/A'])}"
        if target.banner:
            embed.set_image(url=target.banner.url)
        await ctx.reply(ctx.author.mention, embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    @Context.with_type
    async def invite(self, ctx: Context):
        """Get the invite of the bot! Thanks for seeing this command."""
        url = self.bot.invite
        em: discord.Embed = (
            discord.Embed(
                title="Click here to add",
                description=f"```ini\n[Default Prefix: `@{self.bot.user}`]\n```\n**Bot Owned and created by `{self.bot.author_name}`**",
                url=url,
                timestamp=discord.utils.utcnow(),
            )
            .set_footer(text=f"{ctx.author}")
            .set_thumbnail(url=ctx.guild.me.display_avatar.url)
        )
        await ctx.reply(embed=em)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    @Context.with_type
    async def roleinfo(self, ctx: Context, *, role: discord.Role):
        """To get the info regarding the server role."""
        embed = discord.Embed(
            title=f"Role Information: {role.name}",
            description=f"ID: `{role.id}`",
            color=role.color,
            timestamp=discord.utils.utcnow(),
        )
        data = [
            ("Created At", f"{discord.utils.format_dt(role.created_at)}", True),
            ("Is Hoisted?", role.hoist, True),
            ("Position", role.position, True),
            ("Managed", role.managed, True),
            ("Mentionalble?", role.mentionable, True),
            ("Members", len(role.members), True),
            ("Mention", role.mention, True),
            ("Is Boost role?", role.is_premium_subscriber(), True),
            ("Is Bot role?", role.is_bot_managed(), True),
        ]
        for name, value, inline in data:
            embed.add_field(name=name, value=value, inline=inline)
        perms = []
        if role.permissions.administrator:
            perms.append("Administrator")
        if role.permissions.kick_members and role.permissions.ban_members and role.permissions.manage_messages:
            perms.append("Server Moderator")
        if role.permissions.manage_guild:
            perms.append("Server Manager")
        if role.permissions.manage_roles:
            perms.append("Role Manager")
        if role.permissions.moderate_members:
            perms.append("Can Timeout Members")
        if role.permissions.manage_channels:
            perms.append("Channel Manager")
        if role.permissions.manage_emojis:
            perms.append("Emoji Manager")
        embed.description = f"Key perms: {', '.join(perms or ['N/A'])}"
        embed.set_footer(text=f"ID: {role.id}")
        if role.unicode_emoji:
            embed.set_thumbnail(
                url=f"https://raw.githubusercontent.com/iamcal/emoji-data/master/img-twitter-72/{ord(list(role.unicode_emoji)[0]):x}.png",
            )
        if role.icon:
            embed.set_thumbnail(url=role.icon.url)
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    @Context.with_type
    async def emojiinfo(self, ctx: Context, *, emoji: discord.Emoji):
        """To get the info regarding the server emoji."""
        em = discord.Embed(
            title="Emoji Info",
            description=f"\N{BULLET} [Download the emoji]({emoji.url})\n\N{BULLET} Emoji ID: `{emoji.id}`",
            timestamp=discord.utils.utcnow(),
            color=ctx.author.color,
        )
        data = [
            ("Name", emoji.name, True),
            ("Is Animated?", emoji.animated, True),
            ("Created At", f"{discord.utils.format_dt(emoji.created_at)}", True),
            ("Server Owned", emoji.guild.name if emoji.guild else "N/A", True),
            ("Server ID", emoji.guild_id, True),
            ("Created By", emoji.user or "User Not Found", True),
            ("Available?", emoji.available, True),
            ("Managed by Twitch/YouTube?", emoji.managed, True),
            ("Require Colons?", emoji.require_colons, True),
        ]

        em.set_thumbnail(url=emoji.url)
        for name, value, inline in data:
            em.add_field(name=name, value=f"{value}", inline=inline)
        await ctx.reply(embed=em)

    @commands.command(name="channelinfo")
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    @Context.with_type
    async def channel_info(
        self,
        ctx: Context,
        *,
        channel: discord.TextChannel | discord.VoiceChannel | discord.CategoryChannel | discord.StageChannel = None,
    ):
        channel = channel or ctx.channel  # type: ignore
        _id = channel.id  # type: ignore

        assert isinstance(
            channel,
            discord.TextChannel | discord.VoiceChannel | discord.CategoryChannel | discord.StageChannel,
        )

        created_at = f"{discord.utils.format_dt(channel.created_at)}"
        mention = channel.mention
        position = channel.position
        _type = str(channel.type).capitalize()
        embed = (
            discord.Embed(
                title="Channel Info",
                color=ctx.author.color,
                timestamp=discord.utils.utcnow(),
            )
            .add_field(name="Name", value=channel.name)
            .add_field(name="ID", value=f"{_id}")
            .add_field(name="Created At", value=created_at)
            .add_field(name="Mention", value=mention)
            .add_field(name="Position", value=position)
            .add_field(name="Type", value=_type)
            .set_footer(text=f"{ctx.author}")
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    @Context.with_type
    async def request(self, ctx: Context, *, text: str):
        """To request directly from the owner."""
        view = await ctx.prompt(
            f"{ctx.author.mention} are you sure want to request for the same. Abuse of this feature may result in ban from using Parrot bot. Press `YES` to continue",
        )
        if view is None:
            await ctx.reply(f"{ctx.author.mention} you did not responds on time. No request is being sent!")
        elif view:
            if self.bot.author_obj:
                await self.bot.author_obj.send(
                    f"**{ctx.author}** [`{ctx.author.id}`]\n>>> {text[:1800:]}",
                )  # pepole spams T_T
            else:
                from utilities.config import SUPER_USER

                await self.bot.get_user(int(SUPER_USER)).send(text[:1800:])  # type: ignore
            await ctx.reply(f"{ctx.author.mention} your message is being delivered!")
        else:
            await ctx.reply(f"{ctx.author.mention} nvm, reverting the process")

    @commands.command(hidden=True)
    async def hello(self, ctx: Context):
        """Displays my intro message."""
        await ctx.reply(f"Hello! {self.bot.user} is a robot. `{self.bot.author_name}` made me.")

    @commands.command(rest_is_raw=True, hidden=True)
    @commands.is_owner()
    async def echo(self, ctx: Context, *, content):
        await ctx.send(content)

    @commands.command(hidden=True)
    async def cud(self, ctx: Context):
        """Pls no spam."""
        for i in range(3):
            await ctx.send(3 - i)
            await ctx.release(1)

        await ctx.send("go")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    @Context.with_type
    async def announcement(self, ctx: Context):
        """To get the latest news from the support server | Change Log."""
        change_log: discord.Message = await self.bot.change_log()
        embed = discord.Embed(
            title="Announcement",
            timestamp=change_log.created_at,
            color=ctx.author.color,
            description=f"{change_log.content}",
        ).set_footer(text=f"Message by: {ctx.author}")
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    @Context.with_type
    async def vote(self, ctx: Context):
        """Vote the bot for better discovery on top.gg."""
        embed = discord.Embed(
            title="Click here to vote!",
            url=f"https://top.gg/bot/{self.bot.user.id}/vote",
            description=f"**{ctx.author}** thank you for using this command!\n\nYou can vote in every 12h",
            timestamp=discord.utils.utcnow(),
            color=ctx.author.color,
        )
        embed.set_footer(text=f"{ctx.author}")
        embed.set_thumbnail(url=ctx.guild.me.display_avatar.url)
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(embed_links=True)
    @Context.with_type
    async def inviteinfo(self, ctx: Context, code: str):
        """Get the info regarding the Invite Link."""
        invite = await self.bot.fetch_invite(f"https://discord.gg/{code}")
        if (not invite.guild) or (not invite):
            return await ctx.send(f"{ctx.author.mention} invalid invite or invite link is not of server")
        embed = discord.Embed(title=invite.url, timestamp=discord.utils.utcnow(), url=invite.url)
        fields: list[tuple[str, str | None, bool]] = [  # type: ignore
            ("Member count?", invite.approximate_member_count, True),
            ("Presence Count?", invite.approximate_presence_count, True),
            ("Channel", f"<#{invite.channel.id}>" if invite.channel else "N/A", True),
            (
                "Created At",
                discord.utils.format_dt(invite.created_at, "R") if invite.created_at is not None else "Can not determine",
                True,
            ),
            (
                "Expires At",
                discord.utils.format_dt(invite.expires_at, "R") if invite.expires_at is not None else "Can not determine",
                True,
            ),
            (
                "Temporary?",
                invite.temporary if invite.temporary is not None else "Can not determine",
                True,
            ),
            (
                "Max Age",
                invite.max_age or "Infinite" if invite.max_age is not None else "Can not determine",
                True,
            ),
            ("Link", invite.url, True),
            ("Inviter?", invite.inviter, True),
        ]
        for name, value, inline in fields:
            embed.add_field(name=name, value=f"**{value}**", inline=inline)
        await ctx.send(embed=embed)

    @commands.command(aliases=["sticker-info"])
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    @Context.with_type
    async def stickerinfo(self, ctx: Context, sticker: discord.GuildSticker | None = None):
        """Get the info regarding the Sticker."""
        if sticker is None and not ctx.message.stickers:
            return await ctx.error(f"{ctx.author.mention} you did not provide any sticker")
        sticker = sticker or await ctx.message.stickers[0].fetch()
        if sticker is None or (sticker.guild and sticker.guild.id != ctx.guild.id):
            return await ctx.error(f"{ctx.author.mention} this sticker is not from this server")

        embed: discord.Embed = (
            discord.Embed(title="Sticker Info", timestamp=discord.utils.utcnow(), url=sticker.url)
            .add_field(
                name="Name",
                value=sticker.name,
                inline=True,
            )
            .add_field(
                name="ID",
                value=sticker.id,
                inline=True,
            )
            .add_field(
                name="Created At",
                value=discord.utils.format_dt(sticker.created_at),
                inline=True,
            )
            .add_field(
                name="User",
                value=sticker.user.mention,
                inline=True,
            )
            .add_field(
                name="Available",
                value=sticker.available,
                inline=True,
            )
            .add_field(
                name="Emoji",
                value=sticker.emoji,
                inline=True,
            )
            .set_thumbnail(
                url=sticker.url,
            )
            .set_footer(
                text=f"{ctx.author}",
            )
        )
        embed.description = f"""`Description:` **{sticker.description}**"""
        await ctx.send(embed=embed)
