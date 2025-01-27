from __future__ import annotations

from typing import Any

from tabulate import tabulate  # type: ignore

import discord
from core import Cog, Context, Parrot
from discord.ext import commands, tasks
from utilities.deco import with_role

STAFF_ROLES = [771025632184369152, 793531029184708639]


class Sports(Cog):
    """Sports related commands. This category is only for requested servers."""

    def __init__(self, bot: Parrot) -> None:
        self.bot = bot

        # ipl url - the url to the ipl score page.
        # to my localhost to be honest.
        self.url = None
        self.ON_TESTING = False
        # list of channels
        self.channels: list[discord.TextChannel] = []
        self.annouce_task.start()

        self.data = None

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name="\N{CRICKET BAT AND BALL}")

    def create_embed_ipl(
        self,
        *,
        data: dict[str, Any],
    ) -> discord.Embed:
        """To create the embed for the ipl score. For more detailed information, see https://github.com/rtk-rnjn/cricbuzz_scraper."""
        if data["title"]:
            embed = discord.Embed(title=data["title"], timestamp=discord.utils.utcnow())
        embed.set_footer(text=data["status"])

        table1 = tabulate(data["batting"], headers="keys")
        table2 = tabulate(data["bowling"], headers="keys")
        extra = ""
        if extra_ := data.get("extra"):
            for temp in extra_:
                extra += "".join(temp) + "\n"
        if crr := "\n".join(data["crr"]):
            embed.description = f"""
> `{data['team_one']} | {data['team_two']}`
```
{crr}
```
{extra}
"""
        if data.get("batting"):
            embed.add_field(name="Batting - Stats", value=f"```\n{table1}```", inline=False)

        if data.get("bowling"):
            embed.add_field(name="Bowling - Stats", value=f"```\n{table2}```", inline=False)

        embed.add_field(
            name="Recent Commentry",
            value="- " + "\n - ".join(i for i in data["commentry"][:2] if i),
            inline=False,
        )
        return embed

    @commands.group(name="ipl", invoke_without_command=True)
    async def ipl(self, ctx: Context) -> None:
        """To get the IPL score."""
        if ctx.invoked_subcommand is not None:
            return
        if not self.url:
            await ctx.send(f"{ctx.author.mention} No IPL score page set | Ask for it in support server")
            return

        if self.data is None:
            url = f"http://127.0.0.1:1729/cricket_api?url={self.url}"
            response = await self.bot.http_session.get(url)
            if response.status != 200:
                return await ctx.send(
                    f"{ctx.author.mention} Could not get IPL score | Ask for it in support server | Status code: {response.status}",
                )
            self.data = await response.json()

        embed = self.create_embed_ipl(data=self.data)
        await ctx.send(embed=embed)

    @with_role(*STAFF_ROLES)
    @ipl.command(name="set")
    async def set_ipl_url(self, ctx: Context, *, url: str) -> None:
        """Set the IPL score page url."""
        if url.startswith(("<", "[")) and url.endswith((">", "]")):
            url = url[1:-1]

        self.url = url
        await ctx.send(f"Set IPL score page to <{url}>")

    @ipl.command(name="add")
    @commands.is_owner()
    async def add_channel(self, ctx: Context, *, channel: discord.TextChannel):
        """To add the channel to the list of channels to get IPL score."""
        if channel.id in self.channels:
            return await ctx.send(f"{ctx.author.mention} Channel already added")

        self.channels.append(channel)
        await ctx.send(f"{ctx.author.mention} Channel added")

    @ipl.command(name="remove")
    @commands.is_owner()
    async def remove_channel(self, ctx: Context, *, channel: discord.TextChannel):
        """To remove the channel from the list of channels to get IPL score."""
        if channel.id not in self.channels:
            return await ctx.send(f"{ctx.author.mention} Channel not added")

        self.channels.remove(channel)
        await ctx.send(f"{ctx.author.mention} Channel removed")

    @tasks.loop(seconds=90)
    async def annouce_task(
        self,
    ):
        if self.url is None:
            return

        url = f"http://127.0.0.1:1729/cricket_api?url={self.url}"
        response = await self.bot.http_session.get(url)

        if response.status != 200:
            return

        data = await response.json()

        if data == self.data:
            return

        if self.data is None:
            self.data = data

        embed = self.create_embed_ipl(data=data)

        for channel in self.channels:
            await channel.send(embed=embed)
        self.data = data

    async def cog_unload(
        self,
    ):
        self.annouce_task.cancel()
