import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context


class Owner(commands.Cog, name="owner"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="sync",
        description="Synchonizes the slash commands.",
    )
    @app_commands.describe(scope="The scope of the sync. Can be `global` or `guild`")
    @app_commands.default_permissions(administrator=True)
    @commands.is_owner()
    async def sync(self, context: Context, scope: str) -> None:
        """
        Synchonizes the slash commands.

        :param context: The command context.
        :param scope: The scope of the sync. Can be `global` or `guild`.
        """

        if scope == "global":
            try:
                await self.bot.change_presence(activity=discord.Activity(name="Syncing..."), status=discord.Status.idle)
                await context.bot.tree.sync()
                embed = discord.Embed(
                    description="Slash commands have been globally synchronized.",
                    color=0xBEBEFE,
                )
                await context.send(embed=embed, ephemeral=True)
            finally:
                await self.bot.change_presence(activity=discord.Game(name="My Singing Monsters"), status=discord.Status.online)
            return
        elif scope == "guild":
            try:
                await self.bot.change_presence(activity=discord.Activity(name="Syncing..."), status=discord.Status.idle)
                context.bot.tree.copy_global_to(guild=context.guild)
                await context.bot.tree.sync(guild=context.guild)
                embed = discord.Embed(
                    description="Slash commands have been synchronized in this guild.",
                    color=0xBEBEFE,
                )
                await context.send(embed=embed, ephemeral=True)
            finally:
                await self.bot.change_presence(activity=discord.Game(name="My Singing Monsters"), status=discord.Status.online)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="unsync",
        description="Unsynchonizes the slash commands.",
    )
    @app_commands.describe(
        scope="The scope of the sync. Can be `global`, `current_guild` or `guild`"
    )
    @app_commands.default_permissions(administrator=True)
    @commands.is_owner()
    async def unsync(self, context: Context, scope: str) -> None:
        """
        Unsynchonizes the slash commands.

        :param context: The command context.
        :param scope: The scope of the sync. Can be `global`, `current_guild` or `guild`.
        """

        if scope == "global":
            try:
                await self.bot.change_presence(activity=discord.Activity(name="Syncing..."), status=discord.Status.idle)
                context.bot.tree.clear_commands(guild=None)
                await context.bot.tree.sync()
                embed = discord.Embed(
                    description="Slash commands have been globally unsynchronized.",
                    color=0xBEBEFE,
                )
                await context.send(embed=embed, ephemeral=True)
            finally:
                await self.bot.change_presence(activity=discord.Game(name="My Singing Monsters"), status=discord.Status.online)
            return
        elif scope == "guild":
            try:
                await self.bot.change_presence(activity=discord.Activity(name="Syncing..."), status=discord.Status.idle)
                context.bot.tree.clear_commands(guild=context.guild)
                await context.bot.tree.sync(guild=context.guild)
                embed = discord.Embed(
                    description="Slash commands have been unsynchronized in this guild.",
                    color=0xBEBEFE,
                )
                await context.send(embed=embed, ephemeral=True)
            finally:
                await self.bot.change_presence(activity=discord.Game(name="My Singing Monsters"), status=discord.Status.online)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="resync",
        description="Unsynchonizes and then synchonizes the slash commands.",
    )
    @app_commands.describe(scope="The scope of the resync. Can be `global` or `guild`")
    @app_commands.default_permissions(administrator=True)
    @commands.is_owner()
    async def resync(self, context: Context, scope: str) -> None:
        """
        Unsynchonizes and then synchonizes the slash commands.

        :param context: The command context.
        :param scope: The scope of the resync. Can be `global` or `guild`.
        """

        if scope == "global":
            try:
                await self.bot.change_presence(activity=discord.Activity(name="Syncing..."), status=discord.Status.idle)
                context.bot.tree.clear_commands(guild=None)
                await context.bot.tree.sync()
                embed = discord.Embed(
                    description="Slash commands have been globally resynchronized.",
                    color=0xBEBEFE,
                )
                await context.send(embed=embed, ephemeral=True)
            finally:
                await self.bot.change_presence(activity=discord.Game(name="My Singing Monsters"), status=discord.Status.online)
            return
        elif scope == "guild":
            try:
                await self.bot.change_presence(activity=discord.Activity(name="Syncing..."), status=discord.Status.idle)
                context.bot.tree.clear_commands(guild=context.guild)
                await context.bot.tree.sync(guild=context.guild)
                embed = discord.Embed(
                    description="Slash commands have been resynchronized in this guild.",
                    color=0xBEBEFE,
                )
                await context.send(embed=embed, ephemeral=True)
            finally:
                await self.bot.change_presence(activity=discord.Game(name="My Singing Monsters"), status=discord.Status.online)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="load",
        description="Load a cog",
    )
    @app_commands.describe(cog="The name of the cog to load")
    @app_commands.default_permissions(administrator=True)
    @commands.is_owner()
    async def load(self, context: Context, cog: str) -> None:
        """
        The bot will load the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to load.
        """
        try:
            await self.bot.load_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not load the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(
            description=f"Successfully loaded the `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="unload",
        description="Unloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to unload")
    @app_commands.default_permissions(administrator=True)
    @commands.is_owner()
    async def unload(self, context: Context, cog: str) -> None:
        """
        The bot will unload the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to unload.
        """
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not unload the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(
            description=f"Successfully unloaded the `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="reload",
        description="Reloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to reload")
    @app_commands.default_permissions(administrator=True)
    @commands.is_owner()
    async def reload(self, context: Context, cog: str) -> None:
        """
        The bot will reload the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to reload.
        """
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not reload the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(
            description=f"Successfully reloaded the `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="shutdown",
        description="Make the bot shutdown.",
    )
    @app_commands.default_permissions(administrator=True)
    @commands.is_owner()
    async def shutdown(self, context: Context) -> None:
        """
        Shuts down the bot.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(description="Shutting down. Bye! :wave:", color=0xBEBEFE)
        await context.send(embed=embed, ephemeral=True)
        await self.bot.close()


async def setup(bot) -> None:
    await bot.add_cog(Owner(bot))
