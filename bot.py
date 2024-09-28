from json import load
from logging import (
    Formatter,
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL,
    getLogger,
    StreamHandler,
    FileHandler,
)
from os import name, getenv, listdir
from os.path import realpath, dirname, isfile
from platform import python_version, system, release
from sys import exit

from aiosqlite import connect
from discord import Status, Game, Embed, Intents, Message, __version__
from discord.ext import commands, tasks
from discord.ext.commands import Context
from dotenv import load_dotenv

from database import DatabaseManager

if not isfile(f"{realpath(dirname(__file__))}/config.json"):
    exit("'config.json' not found! Please add it and try again.")
else:
    with open(f"{realpath(dirname(__file__))}/config.json") as file:
        config = load(file)

"""	
Setup bot intents (events restrictions)
For more information about intents, please go to the following websites:
https://discordpy.readthedocs.io/en/latest/intents.html
https://discordpy.readthedocs.io/en/latest/intents.html#privileged-intents


Default Intents:
intents.bans = True
intents.dm_messages = True
intents.dm_reactions = True
intents.dm_typing = True
intents.emojis = True
intents.emojis_and_stickers = True
intents.guild_messages = True
intents.guild_reactions = True
intents.guild_scheduled_events = True
intents.guild_typing = True
intents.guilds = True
intents.integrations = True
intents.invites = True
intents.messages = True # `message_content` is required to get the content of the messages
intents.reactions = True
intents.typing = True
intents.voice_states = True
intents.webhooks = True

Privileged Intents (Needs to be enabled on developer portal of Discord), please use them only if you need them:
intents.members = True
intents.message_content = True
intents.presences = True
"""

intents = Intents.all()


class LoggingFormatter(Formatter):
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        DEBUG: gray + bold,
        INFO: blue + bold,
        WARNING: yellow + bold,
        ERROR: red,
        CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        log_format = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}"
        log_format = log_format.replace("(black)", self.black + self.bold)
        log_format = log_format.replace("(reset)", self.reset)
        log_format = log_format.replace("(levelcolor)", log_color)
        log_format = log_format.replace("(green)", self.green + self.bold)
        formatter = Formatter(log_format, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)


logger = getLogger("Humbot")
logger.setLevel(INFO)

console_handler = StreamHandler()
console_handler.setFormatter(LoggingFormatter())
file_handler = FileHandler(filename="discord.log", encoding="utf-8", mode="w")
file_handler_formatter = Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
)
file_handler.setFormatter(file_handler_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or(config["prefix"]),  # noqa
            intents=intents,
            help_command=None,
            status=Status.do_not_disturb,
            activity=Game(name="Starting..."),
        )
        """
        This creates custom bot variables so that we can access these variables in cogs more easily.

        For example, The config is available using the following code:
        - self.config # In this class
        - bot.config # In this file
        - self.bot.config # In cogs
        """
        self.logger = logger
        self.config = config
        self.database = None

    async def init_db(self) -> None:
        async with connect(f"{realpath(dirname(__file__))}/database/database.db") as db:
            with open(f"{realpath(dirname(__file__))}/database/schema.sql") as db_file:
                await db.executescript(db_file.read())
            await db.commit()

    async def load_cogs(self) -> None:
        """
        The code in this function is executed whenever the bot will start.
        """
        for cog_file in listdir(f"{realpath(dirname(__file__))}/cogs"):
            if cog_file.endswith(".py"):
                extension = cog_file[:-3]
                try:
                    await self.load_extension(f"cogs.{extension}")
                    self.logger.info(f"Loaded extension '{extension}'")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    self.logger.error(
                        f"Failed to load extension {extension}\n{exception}"
                    )
        self.logger.info("-------------------")

    async def setup_hook(self) -> None:
        """
        This will just be executed when the bot starts the first time.
        """
        self.logger.info("-------------------")
        self.logger.info(f"Logged in as {self.user.name}")
        self.logger.info(f"discord.py API version: {__version__}")
        self.logger.info(f"Python version: {python_version()}")
        self.logger.info(f"Running on: {system()} {release()} ({name})")
        self.logger.info("-------------------")
        await self.init_db()
        await self.load_cogs()
        self.sync_task.start()
        self.database = DatabaseManager(
            connection=await connect(
                f"{realpath(dirname(__file__))}/database/database.db"
            )
        )

    async def bot_sync(self) -> None:
        await self.change_presence(activity=Game(name="Syncing..."), status=Status.idle)
        await self.tree.sync()
        for guild in self.guilds:
            await self.tree.sync(guild=guild)
        await self.change_presence(
            activity=Game(name="Ready!"),
            status=Status.online,
        )
        self.logger.info("Slash commands synced")

    @tasks.loop(hours=1.0)
    async def sync_task(self) -> None:
        """
        Set up the sync task of the bot.
        """
        await self.bot_sync()

    @sync_task.before_loop
    async def before_sync_task(self) -> None:
        """
        Before starting the sync task, we make sure the bot is ready
        """
        await self.wait_until_ready()

    async def on_message(self, message: Message) -> None:
        """
        The code in this event is executed every time someone sends a message, with or without the prefix

        :param message: The message that was sent.
        """
        if message.author == self.user or message.author.bot:
            return
        await self.process_commands(message)

    async def on_command_completion(self, context: Context) -> None:
        """
        The code in this event is executed every time a normal command has been *successfully* executed.

        :param context: The context of the command that has been executed.
        """
        full_command_name = context.command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])
        if context.guild is not None:
            self.logger.info(
                f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})"
            )
        else:
            self.logger.info(
                f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs"
            )

    async def on_command_error(self, context: Context, error) -> None:
        """
        The code in this event is executed every time a normal valid command catches an error.

        :param context: The context of the normal command that failed executing.
        :param error: The error that has been faced.
        """
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours = hours % 24
            embed = Embed(
                title="Error",
                description=f"**Please slow down** - You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
                color=0xE02B2B,
            )
            await context.send(embed=embed, ephemeral=True)
        elif isinstance(error, commands.NotOwner):
            embed = Embed(
                title="Error",
                description="You are not the owner of the bot!",
                color=0xE02B2B,
            )
            await context.send(embed=embed, ephemeral=True)
            if context.guild:
                self.logger.warning(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is not an owner of the bot."
                )
            else:
                self.logger.warning(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the bot's DMs, but the user is not an owner of the bot."
                )
        elif isinstance(error, commands.MissingPermissions):
            embed = Embed(
                title="Error",
                description="You are missing the permission(s) `"
                + ", ".join(error.missing_permissions)
                + "` to execute this command!",
                color=0xE02B2B,
            )
            await context.send(embed=embed, ephemeral=True)
        elif isinstance(error, commands.BotMissingPermissions):
            embed = Embed(
                title="Error",
                description="I am missing the permission(s) `"
                + ", ".join(error.missing_permissions)
                + "` to fully perform this command!",
                color=0xE02B2B,
            )
            await context.send(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = Embed(
                title="Error",
                description=f"Reason: {error}",
                color=0xE02B2B,
            )
            await context.send(embed=embed, ephemeral=True)
        else:
            raise error


load_dotenv()

bot = DiscordBot()
bot.run(getenv("TOKEN"))
