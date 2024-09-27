import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context


class MySingingMonsters(commands.Cog, name="mysingingmonsters"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.context_menu_user = app_commands.ContextMenu(
            name="Get BBB ID", callback=self.get_bbb_id
        )
        self.bot.tree.add_command(self.context_menu_user)

    async def get_bbb_id(
            self, interaction: discord.Interaction, user: discord.User
    ) -> None:
        """
        Grabs the ID of the user.

        :param interaction: The application command interaction.
        :param user: The user that is being interacted with.
        """
        bbb_info = await self.bot.database.get_bbb_id(user.id)
        if bbb_info:
            bbb_id, bbb_name = bbb_info
            description = f"The BBB ID of {user.mention} is `{bbb_id}` and the name is `{bbb_name}`."
        else:
            description = f"No BBB ID found for {user.mention}."

        embed = discord.Embed(
            title=f"Info for {user.mention}",
            description=description,
            color=0xBEBEFE,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="link",
        description="Link a BBB ID (friend code) to your Discord account.",
    )
    @app_commands.describe(bbb_id="The BBB ID to link.", bbb_name="The BBB name to link.")
    async def link(self, context: Context, bbb_id: str, bbb_name: str) -> None:
        """
        Link a BBB ID (friend code) to your Discord account.

        :param context: The application command context.
        :param bbb_id: The BBB ID to link.
        :param bbb_name: The BBB name to link.
        """
        success = await self.bot.database.set_bbb_id(context.author.id, bbb_id, bbb_name)
        if success:
            description = f"Successfully linked BBB ID `{bbb_id}` with name `{bbb_name}` to your account."
        else:
            description = f"Failed to link BBB ID. It might already be linked to your account."

        embed = discord.Embed(
            title="Link status",
            description=description,
            color=0xBEBEFE,
        )
        await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="unlink",
        description="Unlink a BBB ID (friend code) from your Discord account.",
    )
    async def unlink(self, context: Context) -> None:
        """
        Unlink a BBB ID (friend code) from your Discord account.

        :param context: The application command context.
        """
        success = await self.bot.database.remove_bbb_id(context.author.id)
        if success:
            description = "Successfully unlinked your BBB ID from your account."
        else:
            description = "Failed to unlink BBB ID. It might not be linked to your account."

        embed = discord.Embed(
            title="Link status",
            description=description,
            color=0xBEBEFE,
        )
        await context.send(embed=embed, ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(MySingingMonsters(bot))
