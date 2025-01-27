from __future__ import annotations

import asyncio
import urllib.parse
from functools import partial
from typing import Any

from bs4 import BeautifulSoup

import discord
from core import Context

try:
    import lxml  # noqa: F401  # pylint: disable=unused-import

    HTML_PARSER = "lxml"
except ImportError:
    HTML_PARSER = "html.parser"


def get_ele(soup: BeautifulSoup, name: str, **kw: Any):
    return soup.find_all(name, **kw)


async def python_doc(ctx: Context, text: str) -> discord.Message | None:
    """Filters python.org results based on your query."""
    text = text.strip("`")

    url = "https://docs.python.org/3/genindex-all.html"

    response = await ctx.bot.http_session.get(url)
    if response.status != 200:
        return await ctx.send(f"An error occurred (status code: {response.status}). Retry later.")

    soup = BeautifulSoup(str(await response.text()), HTML_PARSER)  # icantinstalllxmlinheroku

    def soup_match(tag):
        return all(string in tag.text for string in text.strip().split()) and tag.name == "li"

    elements = await asyncio.to_thread(soup.find_all, soup_match, limit=10)
    links = [tag.select_one("li > a") for tag in elements]
    links = [link for link in links if link is not None]

    if not links:
        return await ctx.send(f"{ctx.author.mention} no results")

    content = [f"[{a.string}](https://docs.python.org/3/{a.get('href')})" for a in links]

    emb = discord.Embed(title="Python 3 docs")
    emb.set_thumbnail(
        url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/240px-Python-logo-notext.svg.png",
    )
    emb.description = f"Results for `{text}` :\n" + "\n".join(content)

    return await ctx.send(embed=emb)


async def _cppreference(language: str, ctx: Context, text: str) -> discord.Message | None:
    """Search something on cppreference."""
    text = text.strip("`")

    base_url = f"https://cppreference.com/w/cpp/index.php?title=Special:Search&search={text}"

    url = urllib.parse.quote_plus(base_url, safe=";/?:@&=$,><-[]")

    response = await ctx.bot.http_session.get(url)
    if response.status != 200:
        return await ctx.send(f"An error occurred (status code: {response.status}). Retry later.")

    soup = BeautifulSoup(await response.text(), HTML_PARSER)
    uls = await asyncio.to_thread(soup.find_all, "ul", class_="mw-search-results")

    if not uls:
        return await ctx.send(f"{ctx.author.mention} no results")

    if language == "C":
        wanted = "w/c/"
        url = "https://wikiprogramming.org/wp-content/uploads/2015/05/c-logo-150x150.png"
    else:
        wanted = "w/cpp/"
        url = "https://isocpp.org/files/img/cpp_logo.png"

    for elem in uls:
        if wanted in elem.select_one("a").get("href"):
            links = elem.find_all("a", limit=10)
            break

    content = [f"[{a.string}](https://en.cppreference.com/{a.get('href')})" for a in links]
    emb = discord.Embed(title=f"{language} docs")
    emb.set_thumbnail(url=url)

    emb.description = f"Results for `{text}` :\n" + "\n".join(content)

    return await ctx.send(embed=emb)


c_doc = partial(_cppreference, "C")
cpp_doc = partial(_cppreference, "C++")


async def haskell_doc(ctx: Context, text: str) -> discord.Message | None:
    """Search something on wiki.haskell.org."""
    text = text.strip("`")

    snake = "_".join(text.split(" "))

    base_url = f"https://wiki.haskell.org/index.php?title=Special%3ASearch&profile=default&search={snake}&fulltext=Search"
    url = urllib.parse.quote_plus(base_url, safe=";/?:@&=$,><-[]")

    response = await ctx.bot.http_session.get(url)
    if response.status != 200:
        return await ctx.send(f"An error occurred (status code: {response.status}). Retry later.")

    results = BeautifulSoup(await response.text(), HTML_PARSER).find("div", class_="searchresults")

    if results.find("p", class_="mw-search-nonefound") or not results.find("span", id="Page_title_matches"):
        return await ctx.send(f"{ctx.author.mention} no results")

    # Page_title_matches is first
    ul = results.find("ul", "mw-search-results")

    emb = discord.Embed(title="Haskell docs")
    emb.set_thumbnail(
        url="https://wiki.haskell.org/wikiupload/thumb/4/4a/HaskellLogoStyPreview-1.png/120px-HaskellLogoStyPreview-1.png",
    )

    content = []
    ls = await asyncio.to_thread(ul.find_all, "li", limit=10)
    for li in ls:
        a = li.find("div", class_="mw-search-result-heading").find("a")
        content.append(f"[{a.get('title')}](https://wiki.haskell.org{a.get('href')})")

    emb.description = f"Results for `{text}` :\n" + "\n".join(content)

    return await ctx.send(embed=emb)
