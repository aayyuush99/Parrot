from __future__ import annotations

import asyncio
import datetime
import io
from collections import Counter
from collections.abc import Callable
from typing import Any, Literal

import discord
from core import Context, Parrot
from discord.ext import commands
from utilities.time import FutureTime, ShortTime


async def _add_roles_bot(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    operator: Literal["+", "add", "give", "-", "remove", "take"],
    role: discord.Role,
    reason: str | None,
    **kwargs: Any,
):
    if ctx.author.top_role.position < role.position:
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit the role which is above you")
    if role.permissions.administrator:
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit admin role.")
    is_mod = await ctx.modrole()

    if is_mod and (is_mod.id == role.id):
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit mod role")
    for member in guild.members:
        try:
            if member.bot:
                if operator.lower() in ["+", "add", "give"]:
                    await member.add_roles(role, reason=reason)
                elif operator.lower() in ["-", "remove", "take"]:
                    await member.remove_roles(role, reason=reason)
        except Exception as e:
            await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _add_roles_humans(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    operator: Literal["+", "add", "give", "-", "remove", "take"],
    role: discord.Role,
    reason: str | None,
    **kwargs: Any,
):
    if ctx.author.top_role.position < role.position:
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit the role which is above you")
    if role.permissions.administrator:
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit admin role.")
    is_mod = await ctx.modrole()
    if is_mod and (is_mod.id == role.id):
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit mod role")
    for member in guild.members:
        try:
            if not member.bot:
                if operator.lower() in ["+", "add", "give"]:
                    await member.add_roles(role, reason=reason)
                elif operator.lower() in ["-", "remove", "take"]:
                    await member.remove_roles(role, reason=reason)
        except Exception as e:
            await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _add_roles(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    role: discord.Role,
    reason: str | None,
    **kwargs: Any,
):
    if ctx.author.top_role.position < role.position:
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit the role which is above you")
    if role.permissions.administrator:
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit admin role.")
    is_mod = await ctx.modrole()
    if is_mod and (is_mod.id == role.id):
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit mod role")
    try:
        await member.add_roles(
            role,
            reason=reason,
        )
        await destination.send(f"{ctx.author.mention} given **{role.name} ({role.id})** to **{member.name}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _remove_roles(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    role: discord.Role,
    reason: str | None,
    **kwargs: Any,
):
    if ctx.author.top_role.position < role.position:
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit the role which is above you")
    if role.permissions.administrator:
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit admin role.")
    is_mod = await ctx.modrole()
    if is_mod and (is_mod.id == role.id):
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit mod role")
    try:
        await member.remove_roles(
            role,
            reason=reason,
        )
        await destination.send(f"{ctx.author.mention} removed **{role.name} ({role.id})** from **{member.name}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _role_hoist(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    role: discord.Role,
    _bool: bool,
    reason: str | None,
    **kwargs: Any,
):
    if ctx.author.top_role.position < role.position:
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit the role which is above you")
    if role.permissions.administrator:
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit admin role.")
    is_mod = await ctx.modrole()
    if is_mod and (is_mod.id == role.id):
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit mod role")
    try:
        await role.edit(
            hoist=_bool,
            reason=reason,
        )
        await destination.send(f"{ctx.author.mention} **{role.name} ({role.id})** is now hoisted")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{role.name} ({role.id})**. Error raised: **{e}**")


async def _change_role_name(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    role: discord.Role,
    text: str,
    reason: str | None,
    **kwargs: Any,
):
    if ctx.author.top_role.position < role.position:
        await destination.send(f"{ctx.author.mention} can not assign/remove/edit the role which is above you")
        return
    if role.permissions.administrator:
        await destination.send(f"{ctx.author.mention} can not assign/remove/edit admin role.")
        return
    is_mod = await ctx.modrole()
    if is_mod and (is_mod.id == role.id):
        await destination.send(f"{ctx.author.mention} can not assign/remove/edit mod role")
        return
    try:
        await role.edit(
            name=text,
            reason=reason,
        )
        await destination.send(f"{ctx.author.mention} role name changed to **{text} ({role.id})**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{role.name} ({role.id})**. Error raised: **{e}**")


async def _change_role_color(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    role: discord.Role,
    int_: int,
    reason: str | None,
    **kwargs: Any,
):
    if ctx.author.top_role.position < role.position:
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit the role which is above you")
    if role.permissions.administrator:
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit admin role.")
    is_mod = await ctx.modrole()
    if is_mod and (is_mod.id == role.id):
        return await destination.send(f"{ctx.author.mention} can not assign/remove/edit mod role")
    try:
        await role.edit(color=discord.Color(int_), reason=reason)
        await destination.send(f"{ctx.author.mention} **{role.name} ({role.id})** color changed successfully")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{role.name} ({role.id})**. Error raised: **{e}**")


# BAN


async def _ban(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.User | int,
    days: int = 0,
    reason: str | None,
    silent: bool = False,
    **kwargs: Any,
):
    try:
        if member in (ctx.author.id, guild.me.id, ctx.author, guild.me) and not silent:
            await destination.send(f"{ctx.author.mention} don't do that, Bot is only trying to help")
            return
        await guild.ban(
            discord.Object(member if isinstance(member, int) else member.id),
            reason=reason,
            delete_message_days=days,
        )
        if not silent:
            await destination.send(f"{ctx.author.mention} **{member}** is banned!")
    except Exception as e:
        if not silent:
            await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _mass_ban(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    members: list[discord.Member] | discord.Member,
    days: int = 0,
    reason: str | None,
    **kwargs: Any,
):
    members = members if isinstance(members, list) else [members]
    for member in members:
        if ctx.author.top_role.position < member.top_role.position:
            msg = f"{ctx.author.mention} can not {command_name} the {member}, as the their's role is above you"
            raise commands.BadArgument(
                msg,
            )
        try:
            if member.id in (ctx.author.id, guild.me.id):
                await destination.send(f"{ctx.author.mention} don't do that, Bot is only trying to help")
                return
            await guild.ban(
                member,
                reason=reason,
                delete_message_days=days,
            )
        except Exception as e:
            await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")

    await destination.send(f"{ctx.author.mention} **{', '.join([str(member) for member in members])}** are banned!")


async def _softban(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    members: list[discord.Member] | discord.Member,
    reason: str | None,
    **kwargs: Any,
):
    members = members if isinstance(members, list) else [members]
    for member in members:
        if ctx.author.top_role.position < member.top_role.position:
            msg = f"{ctx.author.mention} can not {command_name} the {member}, as the their's role is above you"
            raise commands.BadArgument(
                msg,
            )
        try:
            if member.id in (ctx.author.id, guild.me.id):
                await destination.send(f"{ctx.author.mention} don't do that, Bot is only trying to help")
                return
            await member.ban(reason=reason)
            await guild.unban(member, reason=reason)

            await destination.send(f"{ctx.author.mention} **{member}** is soft banned!")
        except Exception as e:
            await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _temp_ban(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    members: list[discord.Member] | discord.Member,
    duration: FutureTime | datetime.datetime,
    reason: str | None,
    silent: bool = True,
    bot: Parrot = None,
    **kwargs: Any,
):
    bot = bot or ctx.bot
    members = members if isinstance(members, list) else [members]
    for member in members:
        try:
            if member.id in (ctx.author.id, guild.me.id) and not silent:
                await destination.send(f"{ctx.author.mention} don't do that, Bot is only trying to help")
                return
            await guild.ban(discord.Object(id=member.id), reason=reason)
            mod_action = {
                "action": "UNBAN",
                "member": member.id,
                "reason": f"Action requested by: {ctx.author} ({ctx.author.id}) | Reason: Automatic tempban action",
                "guild": guild.id,
            }

            await ctx.bot.create_timer(
                _event_name="unban",
                expires_at=duration.dt.timestamp(),
                created_at=discord.utils.utcnow().timestamp(),
                message=ctx.message,
                mod_action=mod_action,
            )
            await destination.send(
                f"{ctx.author.mention} **{member}** will be unbanned {discord.utils.format_dt(duration.dt, 'R')}!",
            )

        except Exception as e:
            if not silent:
                await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _unban(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    reason: str | None,
    **kwargs: Any,
):
    try:
        await guild.unban(
            member,
            reason=reason,
        )
        await destination.send(f"{ctx.author.mention} **{member}** is unbanned!")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


# MUTE
async def _timeout(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    _datetime: datetime.datetime,
    reason: str | None,
    silent: bool = False,
    **kwargs: Any,
):
    if ctx.author.top_role.position < member.top_role.position and not silent:
        msg = f"{ctx.author.mention} can not {command_name} the {member}, as the their's role is above you"
        raise commands.BadArgument(
            msg,
        )
    if member.id in (ctx.author.id, guild.me.id) and not silent:
        await destination.send(f"{ctx.author.mention} don't do that, Bot is only trying to help")
        return
    if member.timed_out_until is not None and member.timed_out_until > discord.utils.utcnow():
        return await destination.send(
            f"{ctx.author.mention} **{member}** is already on timeout. It will be removed **{discord.utils.format_dt(member.timed_out_until, 'R')}**",
        )
    try:
        await member.edit(
            timed_out_until=_datetime,
            reason=reason,
        )
        if not silent:
            await destination.send(
                f"{ctx.author.mention} **{member}** is on timeout and will be removed **{discord.utils.format_dt(_datetime, 'R')}**",
            )
    except Exception as e:
        if not silent:
            await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _self_mute(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    _datetime: datetime.datetime,
    reason: str | None,
    **kwargs: Any,
):
    val = await ctx.prompt("Are you sure want to get muted? Don't DM mod for unmute")
    if val:
        try:
            await member.edit(
                timed_out_until=_datetime,
                reason=reason,
            )
            await destination.send(f"**{member}** you will be unmuted **{discord.utils.format_dt(_datetime, 'R')}**")
        except Exception as e:
            await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")
            return

    if val is None:
        await destination.send(f"{ctx.author.mention} you did not respond in time.")

    if val is False:
        return await destination.send(f"{ctx.author.mention} nevermind reverting the process.")


async def _mute(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    reason: str | None,
    silent: bool = False,
    **kwargs: Any,
):
    if ctx.author.top_role.position < member.top_role.position:
        if silent:
            return

        msg = f"{ctx.author.mention} can not {command_name} the {member}, as the their's role is above you"
        raise commands.BadArgument(
            msg,
        )
    if member.id in (ctx.author.id, guild.me.id):
        if silent:
            return

        await destination.send(f"{ctx.author.mention} don't do that, Bot is only trying to help")
        return

    muted = await ctx.muterole() if ctx else await Context.get_mute_role(ctx.bot, guild)

    if not muted:
        muted = await guild.create_role(
            name="Muted",
            reason="Setting up mute role",
            permissions=discord.Permissions(
                send_messages=False,
                add_reactions=False,
                use_application_commands=False,
                create_private_threads=False,
                create_public_threads=False,
                send_messages_in_threads=False,
            ),
        )
        passed, fails = 0, 0
        for channel in guild.channels:
            try:
                if isinstance(channel, discord.TextChannel):
                    await channel.set_permissions(
                        muted,
                        add_reactions=False,
                        use_application_commands=False,
                        create_private_threads=False,
                        create_public_threads=False,
                        send_messages_in_threads=False,
                    )
                if isinstance(channel, discord.CategoryChannel):
                    await channel.set_permissions(
                        muted,
                        add_reactions=False,
                        use_application_commands=False,
                        create_private_threads=False,
                        create_public_threads=False,
                        send_messages_in_threads=False,
                        connect=False,
                        speak=False,
                    )
                if isinstance(channel, discord.VoiceChannel | discord.StageChannel):
                    await channel.set_permissions(muted, connect=False)
                passed += 1
            except discord.HTTPException:
                fails += 1

    try:
        await member.add_roles(
            muted,
            reason=reason,
        )
        if not silent:
            await destination.send(f"{ctx.author.mention} **{member}** is muted!")
        return
    except Exception as e:
        if not silent:
            await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _unmute(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    reason: str | None,
    **kwargs: Any,
):
    if member.timed_out_until:
        try:
            await member.edit(
                timed_out_until=None,
                reason=reason,
            )
            await destination.send(f"{ctx.author.mention} removed timeout from **{member}**")
        except Exception as e:
            await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")

        return
    muted = await ctx.muterole()
    if not muted:
        await destination.send(f"{ctx.author.mention} can not find Mute role in the server")

    try:
        if muted in member.roles:
            await member.remove_roles(
                muted,
                reason=f"Action requested by: {ctx.author.name} ({ctx.author.id}) | Reason: {reason}",
            )
            return await destination.send(f"{ctx.author.mention} **{member}** has been unmuted now!")
        await destination.send(f"{ctx.author.mention} **{member.name}** already unmuted")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _kick(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    reason: str | None,
    silent: bool = False,
    **kwargs: Any,
):
    try:
        if ctx.author.top_role.position < member.top_role.position and not silent:
            msg = f"{ctx.author.mention} can not {command_name} the {member}, as the their's role is above you"
            raise commands.BadArgument(
                msg,
            )
        if member.id in (ctx.author.id, guild.me.id) and not silent:
            await destination.send(f"{ctx.author.mention} don't do that, Bot is only trying to help")
            return
        await member.kick(reason=reason)
        if not silent:
            await destination.send(f"{ctx.author.mention} **{member}** is kicked from the server!")
    except Exception as e:
        if not silent:
            await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _mass_kick(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    members: list[discord.Member] | discord.Member,
    reason: str | None,
    **kwargs: Any,
):
    members = members if isinstance(members, list) else [members]
    for member in members:
        if ctx.author.top_role.position < member.top_role.position:
            msg = f"{ctx.author.mention} can not {command_name} the {member}, as the their's role is above you"
            raise commands.BadArgument(
                msg,
            )
        try:
            if member.id in (ctx.author.id, guild.me.id):
                await destination.send(f"{ctx.author.mention} don't do that, Bot is only trying to help")
                return
            await member.kick(reason=reason)
        except Exception as e:
            await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")

        await asyncio.sleep(0.25)
    await destination.send(
        f"{ctx.author.mention} **{', '.join([str(member) for member in members])}** are kicked from the server!",
    )


# BLOCK


async def _block(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    channel: discord.TextChannel,
    members: list[discord.Member] | discord.Member,
    reason: str | None,
    silent: bool = False,
    **kwargs: Any,
):
    members = members if isinstance(members, list) else [members]
    for member in members:
        if ctx.author.top_role.position < member.top_role.position and not silent:
            msg = f"{ctx.author.mention} can not {command_name} the {member}, as the their's role is above you"
            raise commands.BadArgument(msg)
        try:
            if member.id in (ctx.author.id, guild.me.id) and not silent:
                await destination.send(f"{ctx.author.mention} don't do that, Bot is only trying to help")
                return
            overwrite = channel.overwrites
            try:
                overwrite[member].update(send_messages=False, view_channel=False)
            except KeyError:
                overwrite[member] = discord.PermissionOverwrite(send_messages=False, view_channel=False)
            await channel.edit(overwrites=overwrite, reason=reason)
            if not silent:
                await destination.send(
                    f"{ctx.author.mention} overwrite permission(s) for **{member}** has been created! **View Channel, and Send Messages** is denied!",
                )
        except Exception as e:
            if not silent:
                await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _unblock(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    channel: discord.TextChannel,
    members: list[discord.Member] | discord.Member,
    reason: str | None,
    **kwargs: Any,
):
    members = members if isinstance(members, list) else [members]
    for member in members:
        try:
            if channel.permissions_for(member).send_messages:
                await destination.send(f"{ctx.author.mention} {member.name} is already unblocked. They can send message")
            else:
                overwrite = channel.overwrites
                try:
                    overwrite[member].update(send_messages=None, view_channel=None)
                except KeyError:
                    overwrite[member] = discord.PermissionOverwrite(send_messages=None, view_channel=None)
                await channel.edit(overwrites=overwrite, reason=reason)
            await destination.send(f"{ctx.author.mention} overwrite permission(s) for **{member}** has been deleted!")
        except Exception as e:
            await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


# LOCK


async def _text_lock(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    channel: discord.TextChannel,
    reason: str = None,
    **kwargs: Any,
):
    try:
        overwrite = channel.overwrites
        overwrite[guild.default_role].update(send_messages=False)
        await channel.edit(overwrites=overwrite, reason=reason)
        await destination.send(f"{ctx.author.mention} channel locked.")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{channel.name}**. Error raised: **{e}**")


async def _vc_lock(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    channel: discord.VoiceChannel | discord.StageChannel,
    reason: str = None,
    **kwargs: Any,
):
    if not channel:
        return
    try:
        overwrite = channel.overwrites
        overwrite[guild.default_role].update(connect=False)
        await channel.edit(overwrites=overwrite, reason=reason)
        await destination.send(f"{ctx.author.mention} channel locked.")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{channel.name}**. Error raised: **{e}**")


# UNLOCK


async def _text_unlock(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    channel: discord.TextChannel,
    reason: str = None,
    **kwargs: Any,
):
    try:
        overwrite = channel.overwrites
        overwrite[guild.default_role].update(send_messages=None)
        await channel.edit(overwrites=overwrite, reason=reason)
        await destination.send(f"{ctx.author.mention} channel unlocked.")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{channel.name}**. Error raised: **{e}**")


async def _vc_unlock(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    channel: discord.VoiceChannel | discord.StageChannel,
    reason: str = None,
    **kwargs: Any,
):
    if not channel:
        return
    try:
        overwrite = channel.overwrites
        overwrite[guild.default_role].update(connect=None)
        await channel.edit(overwrites=overwrite, reason=reason)
        await destination.send(f"{ctx.author.mention} channel unlocked.")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{channel.name}**. Error raised: **{e}**")


# EXTRA


async def _change_nickname(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    name: str,
    **kwargs: Any,
):
    if ctx.author.top_role.position < member.top_role.position:
        msg = f"{ctx.author.mention} can not {command_name} the {member}, as the their's role is above you"
        raise commands.BadArgument(
            msg,
        )
    try:
        await member.edit(nick=name, reason=f"Action Requested by {ctx.author} ({ctx.author.id})")
        await destination.send(f"{ctx.author.mention} **{member}** nickname changed to **{name}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _change_channel_topic(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    channel: discord.TextChannel,
    text: str,
    **kwargs: Any,
):
    try:
        await channel.edit(
            topic=text,
            reason=f"Action Requested by {ctx.author} ({ctx.author.id})",
        )
        await destination.send(f"{ctx.author.mention} **{channel.name}** topic changed to **{text}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{channel.name}**. Error raised: **{e}**")


async def _change_channel_name(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    channel: discord.TextChannel,
    text: str,
    **kwargs: Any,
):
    try:
        await channel.edit(name=text, reason=f"Action Requested by {ctx.author} ({ctx.author.id})")
        await destination.send(f"{ctx.author.mention} **{channel}** name changed to **{text}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{channel.name}**. Error raised: **{e}**")


async def _slowmode(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    seconds: int | Literal["off", "disable"],
    channel: discord.TextChannel,
    reason: str | None,
    **kwargs: Any,
):
    if seconds:
        try:
            if 21600 >= seconds > 0:  # discord limit
                await channel.edit(
                    slowmode_delay=seconds,
                    reason=f"Action Requested by {ctx.author} ({ctx.author.id}) | Reason: {reason}",
                )
                return await destination.send(
                    f"{ctx.author.mention} {channel} is now in slowmode of **{seconds}**, to reverse type [p]slowmode 0",
                )
            if seconds == 0 or (seconds.lower() in ("off", "disable")):
                await channel.edit(
                    slowmode_delay=seconds,
                    reason=f"Action Requested by {ctx.author} ({ctx.author.id}) | Reason: {reason}",
                )
                return await destination.send(f"{ctx.author.mention} **{channel}** is now not in slowmode.")
            if (seconds >= 21600) or (seconds < 0):
                return await destination.send(
                    f"{ctx.author.mention} you can't set slowmode in negative numbers or more than 21600 seconds",
                )

        except Exception as e:
            await destination.send(f"Can not able to {command_name} **{channel.name}**. Error raised: **{e}**")


async def _clone(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    channel: discord.TextChannel,
    reason: str | None,
    **kwargs: Any,
):
    try:
        new_channel = await channel.clone(reason=f"Action requested by {ctx.author} ({ctx.author.id}) | Reason: {reason}")
        await channel.delete(reason=f"Action requested by {ctx.author} ({ctx.author.id}) | Reason: {reason}")
        await new_channel.edit(position=channel.position)
        await new_channel.send(f"{ctx.author.mention}", delete_after=5)
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{channel.name}**. Error raised: **{e}**")


# VOICE MOD


async def _voice_mute(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    reason: str | None,
    **kwargs: Any,
):
    if ctx.author.top_role.position < member.top_role.position:
        msg = f"{ctx.author.mention} can not {command_name} the {member}, as the their's role is above you"
        raise commands.BadArgument(msg)
    try:
        await member.edit(mute=True, reason=reason)
        await destination.send(f"{ctx.author.mention} voice muted **{member}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _voice_unmute(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    reason: str | None,
    **kwargs: Any,
):
    try:
        await member.edit(mute=False, reason=reason)
        await destination.send(f"{ctx.author.mention} voice unmuted **{member}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _voice_deafen(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    reason: str | None,
    **kwargs: Any,
):
    if ctx.author.top_role.position < member.top_role.position:
        msg = f"{ctx.author.mention} can not {command_name} the {member}, as the their's role is above you"
        raise commands.BadArgument(msg)
    try:
        await member.edit(deafen=True, reason=reason)
        await destination.send(f"{ctx.author.mention} voice deafened **{member}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _voice_undeafen(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    reason: str | None,
    **kwargs: Any,
):
    try:
        await member.edit(deafen=False, reason=reason)
        await destination.send(f"{ctx.author.mention} voice undeafened **{member}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _voice_kick(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    reason: str | None,
    **kwargs: Any,
):
    if ctx.author.top_role.position < member.top_role.position:
        msg = f"{ctx.author.mention} can not {command_name} the {member}, as the their's role is above you"
        raise commands.BadArgument(msg)
    try:
        await member.edit(voice_channel=None, reason=reason)
        await destination.send(f"{ctx.author.mention} voice kicked **{member}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _voice_ban(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    channel: discord.VoiceChannel | discord.StageChannel,
    reason: str | None,
    **kwargs: Any,
):
    if ctx.author.top_role.position < member.top_role.position:
        msg = f"{ctx.author.mention} can not {command_name} the {member}, as the their's role is above you"
        raise commands.BadArgument(msg)
    try:
        overwrite = channel.overwrites
        try:
            overwrite[member].update(connect=False)
        except KeyError:
            overwrite[member] = discord.PermissionOverwrite(connect=False)
        await channel.edit(overwrites=overwrite, reason=reason)
        await destination.send(f"{ctx.author.mention} voice banned **{member}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _voice_unban(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    member: discord.Member,
    channel: discord.VoiceChannel | discord.StageChannel,
    reason: str | None,
    **kwargs: Any,
):
    try:
        overwrite = channel.overwrites
        try:
            overwrite[member].update(connect=None)
        except KeyError:
            overwrite[member] = discord.PermissionOverwrite(connect=None)
        await destination.send(f"{ctx.author.mention} voice unbanned **{member}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{member}**. Error raised: **{e}**")


async def _sticker_delete(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    sticker: discord.GuildSticker,
    reason: str | None,
    **kwargs: Any,
):
    if sticker.guild and sticker.guild.id != guild.id:
        return await destination.send(
            f"{ctx.author.mention} can not {command_name} the {sticker}, as the sticker is not in this server",
        )

    try:
        await sticker.delete(reason=reason)
        await destination.send(f"{ctx.author.mention} sticker deleted **{sticker}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{sticker.name} {sticker.id}**. Error raised: **{e}**")


async def _sticker_add(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    sticker: discord.GuildSticker,
    reason: str | None,
    **kwargs: Any,
):
    url = sticker.url
    if not url:
        return await destination.send(
            f"{ctx.author.mention} can not {command_name} the {sticker}, as the sticker has no url",
        )
    res = await ctx.bot.http_session.get(url)
    if res.status != 200:
        return await destination.send(
            f"{ctx.author.mention} can not {command_name} the {sticker}, as the sticker has no url",
        )
    raw = await res.read()
    buffer = io.BytesIO(raw)
    file = discord.File(buffer, filename=f"{sticker.name}.png")
    try:
        sticker = await guild.create_sticker(
            name=sticker.name,
            description=kwargs.get("description", f"No description given to the {sticker.name}"),
            emoji=kwargs.get("emoji"),
            file=file,
            reason=reason,
        )
        await destination.send(f"{ctx.author.mention} sticker added **{sticker.name}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{sticker.name} {sticker.id}**. Error raised: **{e}**")


async def _sticker_addurl(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    url: str,
    name: str,
    emoji: str,
    reason: str | None,
    description: str,
    **kwargs: Any,
):
    res = await ctx.bot.http_session.get(url)
    raw = await res.read()
    buffer = io.BytesIO(raw)
    file = discord.File(buffer, filename=f"{name}.png")
    try:
        sticker = await guild.create_sticker(
            name=name,
            description=description,
            emoji=emoji,
            file=file,
            reason=reason,
        )
        await destination.send(f"{ctx.author.mention} sticker added **{sticker.name}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{sticker.name} {sticker.id}**. Error raised: **{e}**")


async def _emoji_delete(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    emojis: list[discord.Emoji | discord.PartialEmoji],
    reason: str | None,
    **kwargs: Any,
):
    for emoji in emojis:
        if emoji.guild.id != guild.id:
            return await destination.send(
                f"{ctx.author.mention} can not {command_name} the {emoji}, as the emoji is not in this server",
            )
        try:
            if emoji.guild.id == guild.id:
                await emoji.delete(reason=f"Action requested by {ctx.author} ({ctx.author.id}) | Reason: {reason}")
                await destination.send(f"{ctx.author.mention} **{emoji}** deleted!")
        except Exception as e:
            await destination.send(f"Can not able to {command_name} **{emoji.name} ({emoji.id})**. Error raised: **{e}**")


async def _emoji_add(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    emojis: list[discord.Emoji | discord.PartialEmoji],
    reason: str | None,
    **kwargs: Any,
):
    for emoji in emojis:
        try:
            res = await ctx.bot.http_session.get(emoji.url)
            raw = await res.read()
            ej = await guild.create_custom_emoji(
                name=emoji.name,
                image=raw,
                reason=reason,
            )
            await destination.send(f"{ctx.author.mention} emoji created {ej}")
        except Exception as e:
            await destination.send(f"Can not able to {command_name} **{emoji.name} ({emoji.id})**. Error raised: **{e}**")


async def _emoji_addurl(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    url: str,
    name: str,
    reason: str | None,
    **kwargs: Any,
):
    try:
        res = await ctx.bot.http_session.get(url)
        raw = await res.read()
        emoji = await guild.create_custom_emoji(name=name, image=raw, reason=reason)
        await destination.send(f"{ctx.author.mention} emoji created {emoji}")
    except Exception as e:
        await destination.send(f"Can not able to {command_name}. Error raised: **{e}**")


async def _emoji_rename(
    *,
    guild: discord.Guild,
    command_name: str,
    ctx: Context,
    destination: discord.abc.Messageable,
    emoji: discord.Emoji,
    name: str,
    reason: str | None,
    **kwargs: Any,
):
    try:
        if emoji.guild.id != guild.id:
            return await destination.send(
                f"{ctx.author.mention} can not {command_name} the {emoji}, as the emoji is not in this server",
            )
        await emoji.edit(name=name, reason=reason)
        await destination.send(f"{ctx.author.mention} {emoji} name edited to **{name}**")
    except Exception as e:
        await destination.send(f"Can not able to {command_name} **{emoji.name} ({emoji.id})**. Error raised: **{e}**")


async def do_removal(
    ctx: Context,
    limit: int | None,
    predicate: Callable[[discord.Message], Any],
    *,
    before: int | None = None,
    after: int | None = None,
):
    limit = max(1, min(limit or 1, 2000))

    passed_before = ctx.message if before is None else discord.Object(id=before)
    passed_after = discord.Object(id=after) if after is not None else None
    try:
        deleted = await ctx.channel.purge(limit=limit, before=passed_before, after=passed_after, check=predicate)
    except discord.HTTPException as e:
        return await ctx.send(f"Can not able to {ctx.command.qualified_name}. Error raised: **{e}** (try a smaller search?)")

    spammers = Counter(m.author.display_name for m in deleted)
    deleted = len(deleted)
    messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
    if deleted:
        messages.append("")
        spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
        messages.extend(f"**{name}**: {count}" for name, count in spammers)

    to_send = "\n".join(messages)

    if len(to_send) > 2000:
        await ctx.send(f"Successfully removed {deleted} messages.", delete_after=10)
    else:
        await ctx.send(to_send, delete_after=10)

    await ctx.message.delete(delay=10)


MEMBER_REACTION: dict[str, Callable] = {
    "\N{HAMMER}": _ban,
    "\N{WOMANS BOOTS}": _kick,
    "\N{ZIPPER-MOUTH FACE}": _mute,
    "\N{GRINNING FACE WITH SMILING EYES}": _unmute,
    "\N{CROSS MARK}": _block,
    "\N{HEAVY LARGE CIRCLE}": _unblock,
    "\N{UPWARDS BLACK ARROW}": _add_roles,
    "\N{DOWNWARDS BLACK ARROW}": _remove_roles,
    "\N{LOWER LEFT FOUNTAIN PEN}": _change_nickname,
}
TEXT_REACTION: dict[str, Callable] = {
    "\N{LOCK}": _text_lock,
    "\N{OPEN LOCK}": _text_unlock,
    "\N{MEMO}": _change_channel_topic,
    "\N{LOWER LEFT FOUNTAIN PEN}": _change_channel_name,
}

VC_REACTION: dict[str, Callable] = {
    "\N{LOCK}": _vc_lock,
    "\N{OPEN LOCK}": _vc_unlock,
    "\N{LOWER LEFT FOUNTAIN PEN}": _change_channel_name,
}

ROLE_REACTION: dict[str, Callable] = {
    "\N{UPWARDS BLACK ARROW}": _role_hoist,
    "\N{DOWNWARDS BLACK ARROW}": _role_hoist,
    "\N{RAINBOW}": _change_role_color,
    "\N{LOWER LEFT FOUNTAIN PEN}": _change_role_name,
}


async def instant_action_parser(*, name: str, ctx: Context, message: discord.Message, **kw: Any):
    PUNISH = [
        "ban",
        "tempban",
        "kick",
        "timeout",
        "mute",
    ]

    if name not in PUNISH:
        return

    if kw.get("duration"):
        try:
            duration = ShortTime(kw["duration"])
        except Exception:
            duration = None
    else:
        duration = None

    if name == "ban":
        try:
            await ctx.guild.ban(message.author, reason="Auto mod: Mention protection")
        except (discord.Forbidden, discord.NotFound):
            pass

    elif name == "kick":
        try:
            await message.author.kick(reason="Auto mod: Mention protection")
        except (discord.Forbidden, discord.NotFound):
            pass

    elif name == "tempban" and duration:
        try:
            await ctx.guild.ban(message.author, reason="Auto mod: Mention protection")
        except (discord.Forbidden, discord.NotFound):
            pass
        else:
            mod_action = {
                "action": "UNBAN",
                "member": message.author.id,
                "reason": "Auto mod: Automatic tempban action",
                "guild": ctx.guild.id,
            }

            await ctx.bot.create_timer(
                _event_name="unban",
                expires_at=duration.dt.timestamp(),
                created_at=discord.utils.utcnow().timestamp(),
                message=ctx.message,
                mod_action=mod_action,
            )

    if name in {"timeout", "mute"}:
        try:
            if duration:
                await message.author.edit(
                    timed_out_until=duration.dt,
                    reason="Auto mod: Mention protection",
                )
            else:
                muted = await ctx.muterole()
                if not muted:
                    return
                await message.author.add_roles(
                    muted,
                    reason="Auto mod: Mention protection",
                )
        except (discord.Forbidden, discord.NotFound):
            pass
