from __future__ import annotations

from .method import Easter
from core import Parrot


async def setup(bot: Parrot) -> None:
    await bot.add_cog(Easter(bot))
