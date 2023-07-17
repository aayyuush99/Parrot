from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Parrot

import discord


class Variables:
    __class__ = None  # type: ignore

    def __init__(self, *, message: discord.Message, bot: Parrot):
        self.__message = message
        self.__bot = bot

    def build_base(self):
        self.message_id = self.__message.id
        self.message_content = self.__message.content

        self.channel_id = self.__message.channel.id
        self.channel_name = self.__message.channel.name  # type: ignore

        self.message_author_id = self.__message.author.id
        self.message_author_name = self.__message.author.name
        self.message_author = str(self.__message.author)

        payload = {
            "message_id": self.message_id,
            "message_content": self.message_content,
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "message_author_id": self.message_author_id,
            "message_author_name": self.message_author_name,
            "message_author": self.message_author,
        }

        self.get_role_name = self._get_role_name
        self.get_channel_name = self._get_channel_name
        self.get_member_name = self._get_member_name
        self.create_channel = self._create_channel
        self.create_role = self._create_role

        payload["get_role_name"] = self.get_role_name
        payload["get_channel_name"] = self.get_channel_name
        payload["get_member_name"] = self.get_member_name
        payload["create_channel"] = self.create_channel

        return payload

    def _get_role_name(self, role_id: int):
        r = self.__message.guild.get_role(role_id)  # type: ignore
        return r.name if r else None

    def _get_channel_name(self, channel_id: int):
        c = self.__message.guild.get_channel(channel_id)  # type: ignore
        return c.name if c else None

    def _get_member_name(self, member_id: int):
        m = self.__message.guild.get_member(member_id)  # type: ignore
        return m.name if m else None

    async def _create_channel(self, name: str, position: int = None, category: int = None):
        cat = (
            self.__message.guild.get_channel(category) if category else None
        )  # type: discord.CategoryChannel # type: ignore
        chn = await self.__message.guild.create_text_channel(  # type: ignore
            name, position=position or discord.utils.MISSING, category=cat
        )
        return chn.id

    async def _create_role(self, name: str, permission: int = None, color: int = None):
        if permission:
            perms = discord.Permissions(permission)
        else:
            perms = discord.Permissions.none()

        clr = discord.Color.from_str(str(color)) if color else discord.Color.default()
        role = await self.__message.guild.create_role(name=name, color=clr, permissions=perms)  # type: ignore
        return role.id


# print(dir(Variables))
