from discord.ext import commands
from discord.ext.commands import Context


class MySingingMonsters(commands.Cog, name="mysingingmonsters"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="link",
        description="Link a BBB ID (friend code) to your Discord account.",
    )
    async def link(self, context: Context) -> None:
        """
        This is a testing command that does nothing.

        :param context: The application command context.
        """
        pass


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot) -> None:
    await bot.add_cog(MySingingMonsters(bot))
