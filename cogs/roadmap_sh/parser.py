from __future__ import annotations

import os
import re

import aiofiles
from jishaku.paginators import PaginatorEmbedInterface

import discord
from core import Context, ParrotView
from discord.ext import commands

folders = {
    "roadmaps": r"extra/tutorials/roadmaps",
    "best": r"extra/tutorials/best-practices",
    "links": r"extra/tutorials/link-groups",
    "videos": r"extra/tutorials/videos",
}


class ParentView(ParrotView):
    message: discord.Message
    ctx: Context

    @discord.ui.button(label="Roadmap", style=discord.ButtonStyle.blurple)
    async def roadmap(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        dirs = [folders["roadmaps"] + "/" + i for i in os.listdir(folders["roadmaps"])]
        _25_dirs, _rest = dirs[:25], dirs[25:]
        select = ContentView(folders=_25_dirs)
        self.add_item(select)

        if _rest:
            select = ContentView(folders=_rest)
            self.add_item(select)

        self.best_practices.disabled = True
        self.link_groups.disabled = True
        self.videos.disabled = True

        await interaction.response.edit_message(embed=self.embed.set_footer(text="Select a folder..."), view=self)

    @discord.ui.button(label="Best Practices", style=discord.ButtonStyle.blurple)
    async def best_practices(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        dirs = [folders["best"] + "/" + i for i in os.listdir(folders["best"])]
        _25_dirs, _rest = dirs[:25], dirs[25:]
        select = ContentView(folders=_25_dirs)
        self.add_item(select)

        if _rest:
            select = ContentView(folders=_rest)
            self.add_item(select)

        self.roadmap.disabled = True
        self.link_groups.disabled = True
        self.videos.disabled = True

        await interaction.response.edit_message(embed=self.embed.set_footer(text="Select a folder..."), view=self)

    @discord.ui.button(label="Link Groups", style=discord.ButtonStyle.blurple)
    async def link_groups(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        dirs = [folders["links"] + "/" + i for i in os.listdir(folders["links"])]
        _25_dirs, _rest = dirs[:25], dirs[25:]

        select = ContentView(folders=_25_dirs)
        self.add_item(select)

        if _rest:
            select = ContentView(folders=_rest)
            self.add_item(select)

        self.roadmap.disabled = True
        self.best_practices.disabled = True
        self.videos.disabled = True

        await interaction.response.edit_message(embed=self.embed.set_footer(text="Select a folder..."), view=self)

    @discord.ui.button(label="Videos", style=discord.ButtonStyle.blurple)
    async def videos(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        dirs = [folders["videos"] + "/" + i for i in os.listdir(folders["videos"])]
        _25_dirs, _rest = dirs[:25], dirs[25:]
        select = ContentView(folders=_25_dirs)
        self.add_item(select)

        if _rest:
            select = ContentView(folders=_rest)
            self.add_item(select)

        self.roadmap.disabled = True
        self.best_practices.disabled = True
        self.link_groups.disabled = True

        await interaction.response.edit_message(embed=self.embed.set_footer(text="Select a folder..."), view=self)

    async def start(self, ctx: Context) -> None:
        self.ctx = ctx
        self.embed = discord.Embed(
            title="Developer Roadmaps",
            description="[roadmap.sh](https://roadmap.sh) is a community effort to create roadmaps, guides and other educational content to help guide developers in picking up a path and guide their learnings.",
            url="https://roadmap.sh/",
        )
        self.message = await ctx.send(
            embed=self.embed,
            view=self,
        )


class ContentView(discord.ui.Select):
    view: ParentView

    def __init__(self, *, folders: list[str]) -> None:
        super().__init__(placeholder="Select a folder...", min_values=1, max_values=1)

        for folder in folders:
            self.add_option(label=folder.replace("-", " ").title(), value=folder)

    def remove_img_links(self, text: str) -> str:
        """Remove all ![]() links from text."""
        return re.sub(r"!\[.*\]\(.*\)", "", text)

    def replace_partial_links(self, text: str) -> str:
        def f(m: re.Match) -> str:
            title, link = m.groups()
            if link.startswith("/"):
                link = f"https://roadmap.sh{link}"
            return f"{title}({link})"

        return re.sub(r"(\[.*?\])\((.*?)\)", f, text)

    async def send_file_embed(self, path: str, interaction: discord.Interaction) -> None:
        async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
            content = await f.read()

        page = commands.Paginator(prefix="", suffix="", max_size=1990)
        _ADD_LINE = True

        for line in content.splitlines():
            if line == "---":
                _ADD_LINE = not _ADD_LINE
                continue
            if _ADD_LINE:
                new_line = self.remove_img_links(line)
                new_line = self.replace_partial_links(new_line)
                page.add_line(new_line)

        if page.pages:
            interference = PaginatorEmbedInterface(self.view.ctx, page, owner=self.view.ctx.author)
            await interference.send_to(interaction.followup)  # type: ignore
        else:
            await interaction.followup.send("No content found.")

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        folder = self.values[0]
        if not os.path.isdir(folder):
            await self.send_file_embed(folder, interaction)
        else:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            files.sort()
            self.view.remove_item(self)
            select = ContentView(folders=[f"{folder}/{i}" for i in files])
            self.view.add_item(select)

            await interaction.followup.send(
                embed=discord.Embed(
                    title="Developer Roadmaps",
                    description="[roadmap.sh](https://roadmap.sh) is a community effort to create roadmaps, guides and other educational content to help guide developers in picking up a path and guide their learnings.",
                    url="https://roadmap.sh/",
                ).set_footer(text="Select a file..."),
                view=self.view,
            )
