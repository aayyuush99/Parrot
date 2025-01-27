from __future__ import annotations

from core import Parrot

from .listeners import SnipeMessageListener
from .mis import Misc


async def setup(bot: Parrot) -> None:
    await bot.add_cog(Misc(bot))
    await bot.add_cog(SnipeMessageListener(bot))
