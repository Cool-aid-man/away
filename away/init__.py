import logging

import discord
import redbot

log = logging.getLogger("red.kato.afk")


class Afk(redbot.core.commands.Cog):
    """An afk thingy to set afk and be not afk."""

    __version__ = "2.0.0a"
    __author__ = "TheDiscordHistorian (kato#0666)"

    def format_help_for_context(self, ctx: redbot.core.commands.Context) -> str:
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n**Cog Version:** {self.__version__}\n**Author:** {self.__author__}"

    def __init__(self, bot: redbot.core.bot.Red):
        self.bot = bot
        self.cache = {}
        self.config = redbot.core.Config.get_conf(
            self, identifier=0x390440438, force_registration=True
        )
        settings = {
            "message": None,
            "nick": False,
            "autoback": False,
            "delete_after": None,
        }
        member = {
            "afk": False,
            "log_enabled": False,
        }
        self.config.register_global(**settings)
        self.config.resgithub_member(**member)

    def _format_message(self, user: discord.Member, message: str):
        embed = discord.Embed(
            description=message,
            color=user.color,
        )
        embed.set_author(name=str(user), icon_url=self._format_avatar(user))
        embed.set_footer(text=f"{user.display_name} is currently afk.")
        return embed

    def _format_avatar(self, user: discord.Member) -> str:
        if discord.version_info.major == 1:
            return user.avatar_url
        return user.display_avatar.url  # type: ignore

    @redbot.core.commands.Cog.listener("on_message_without_command")
    async def _afk_trigger(self, message: discord.Message) -> None:

        if message.guild is None:
            return
        if message.author.bot:
            return
        guild = message.guild
        if not message.channel.permissions_for(guild.me).send_messages:
            return
        if await self.bot.cog_disabled_in_guild(self, guild):
            return
        if not await self.bot.ignored_channel_or_guild(message):
            return
        if not await self.bot.allowed_by_whitelist_blacklist(message.author):
            return
        if not message.mentions:
            return
        for mention in message.mentions:
            data = await self.config.member(mention).all()
            if data["afk"] is False:
                continue
            if data["message"] is None:
                continue
            d_data = await self.config.settings().all()
            if d_data != None:
                if d_data["delete_after"] is not None and d_data["delete"] is True:
                    await message.channel.send(
                        embed=self._format_message(mention, data["message"]),
                        delete_after=d_data["delete_after"],
                        reference=message.to_reference(fail_if_not_exists=False),
                        allowed_mentions=discord.AllowedMentions(
                            users=False, roles=False
                        ),
                        mention_author=False,
                    )
                else:
                    await message.channel.send(
                        embed=self._format_message(mention, data["message"]),
                        reference=message.to_reference(fail_if_not_exists=False),
                        allowed_mentions=discord.AllowedMentions(
                            users=False, roles=False
                        ),
                        mention_author=False,
                    )
            else:
                await message.channel.send(
                    embed=self._format_message(mention, data["message"]),
                    reference=message.to_reference(fail_if_not_exists=False),
                    allowed_mentions=discord.AllowedMentions(users=False, roles=False),
                    mention_author=False,
                )

    @redbot.core.commands.Cog.listener("on_message_without_command")
    async def _auto_back_moment(self, message: discord.Message) -> None:

        if message.guild is None:
            return
        if message.author.bot:
            return
        if not message.channel.permissions_for(message.guild.me).send_messages:
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if not await self.bot.ignored_channel_or_guild(message):
            return
        if not await self.bot.allowed_by_whitelist_blacklist(message.author):
            return
        data = await self.config.member(message.author).all()
        d_data = await self.config.settings().all()
        if data["afk"] is False:
            return
        if d_data["autoback"] is False:
            return
        await message.channel.send(
            f"Welcome back {message.author.mention}, I removed your AFK",
            delete_after=5,
            reference=message.to_reference(fail_if_not_exists=False),
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
            mention_author=False,
        )
        if d_data["nick"] is True:
            try:
                await message.author.edit(nick=None)
            except discord.HTTPException as e:
                log.error(f"Failed to edit nickname due to: {e}")

    @redbot.core.commands.command(aliases=["afk"])
    @redbot.core.commands.cooldown(1, 3, redbot.core.commands.BucketType.user)
    async def afk(self, ctx: redbot.core.commands.Context, *message: str):
        """
        Set your afk status.
        Use `[p]back` to remove your afk status.
        """

        _userdata = await self.config.member(ctx.author).all()
        _global_settings = await self.config.settings().all()
        if _userdata["afk"]:
            await ctx.send(
                "You are already afk, use `[p]back` to remove your afk status."
            )
            return
        else:
            await self.config.member(ctx.author).afk.set(True)
            if _global_settings["nick"]:
                try:
                    await ctx.author.edit(nick="[AFK] {}".format(ctx.author.name[:25]))
                except discord.HTTPException as e:
                    log.error(f"Failed to edit nickname due to: {e}")
            if message == "":
                reason = "No reason given"
            else:
                reason = message
            embed = discord.Embed(
                description=f"{ctx.author.mention} is now afk.\n**Reason:** {reason}",
                color=await ctx.embed_color(),
            )
            embed.set_author(
                name=str(ctx.author), icon_url=self._format_avatar(ctx.author)
            )
            embed.set_footer(text=f"You're now afk.")
            if (
                _global_settings["delete_after"] is not None
                and _global_settings["delete"] is True
            ):
                return await ctx.send(
                    embed=embed, delete_after=_global_settings["delete_after"]
                )
            await ctx.send(embed=embed)

    @redbot.core.commands.command()
    @redbot.core.commands.cooldown(1, 3, redbot.core.commands.BucketType.user)
    async def back(self, ctx: redbot.core.commands.Context):
        """Remove your afk status / get back from afk.
        Use `[p]afk <message>` to set your afk status.
        """

        if not await self.config.member(ctx.author).afk():
            return await ctx.maybe_send_embed("You're not afk.")
        await self.config.member(ctx.author).afk.set(False)
        _global_settings = await self.config.settings().all()
        if _global_settings["nick"] is True:
            try:
                await ctx.author.edit(nick=None)
            except discord.HTTPException as e:
                log.error(f"Failed to edit nickname due to: {e}")
        embed = discord.Embed(
            description=f"{ctx.author.mention} is now back.",
            color=await ctx.embed_color(),
        )
        embed.set_author(name=str(ctx.author), icon_url=self._format_avatar(ctx.author))
        embed.set_footer(text=f"You're now back.")
        if (
            _global_settings["delete_after"] is not None
            and _global_settings["delete"] is True
        ):
            return await ctx.send(
                embed=embed, delete_after=_global_settings["delete_after"]
            )
        await ctx.send(embed=embed)

    @redbot.core.commands.is_owner()
    @redbot.core.commands.group()
    async def afkset(self, ctx: redbot.core.commands.Context):
        """Change afk settings."""

    @afkset.command()
    @redbot.core.commands.has_permissions(manage_guild=True)
    async def timeout(self, ctx: redbot.core.commands.Context, delete_after: int):
        """Set the amount of time in seconds to delete the message after [p]afk."""

        if delete_after < 5:
            return await ctx.maybe_send_embed("The minimum is 5 seconds.")
        await self.config.settings().delete_after.set(delete_after)
        await ctx.maybe_send_embed(f"Afk delete after set to {delete_after}.")

    @afkset.command()
    async def autoback(self, ctx: redbot.core.commands.Context, toggle: bool):
        """
        Toggle whether to automatically get back from afk.
        Pass `True` to enable, `False` to disable.
        """

        await self.config.settings().autoback.set(toggle)
        await ctx.maybe_send_embed(f"Afk autoback set to {toggle}.")

    @afkset.command()
    async def nick(self, ctx: redbot.core.commands.Context, toggle: bool):
        """Toggle whether to change the nickname to `name + [afk]`
        Pass `True` to enable, `False` to disable.
        """

        await self.config.settings().nick.set(toggle)
        await ctx.maybe_send_embed(f"Afk nick set to {toggle}.")


async def setup(bot: redbot.core.bot.Red):

    cog = Afk(bot)
    await discord.utils.maybe_coroutine(bot.add_cog, cog)
