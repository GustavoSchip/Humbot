from datetime import timedelta
from typing import List, Optional

from discord import app_commands, Interaction, User, Embed
from discord.ext import commands
from discord.ext.commands import Context
from pydantic.dataclasses import dataclass


@dataclass
class Element:
    name: str
    description: str
    wiki_url: str


@dataclass
class Island:
    name: str
    description: str
    wiki_url: str


@dataclass
class BreedingIncubation:
    duration: timedelta
    enhanced: bool
    skin_boost: bool


@dataclass
class Monster:
    name: str
    elements: List[Element]
    islands: List[Island]
    description: str
    breeding_incubation: List[BreedingIncubation]
    wiki_url: str


class MySingingMonsters(commands.Cog, name="mysingingmonsters"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.context_menu_user = app_commands.ContextMenu(
            name="Get BBB ID", callback=self.get_bbb_id
        )
        self.bot.tree.add_command(self.context_menu_user)
        self.elements = []
        self.islands = []
        self.monsters = []
        self.load_data()

    def load_data(self):
        self.elements = [Element(**element) for element in self.bot.data["elements"]]
        self.islands = [Island(**island) for island in self.bot.data["islands"]]
        self.monsters = [
            Monster(
                name=monster["name"],
                elements=[
                    self.get_element_by_name(name) for name in monster["elements"]
                ],
                islands=[
                    self.get_island_by_name(name) for name in monster["islands"]
                ],
                description=monster["description"],
                breeding_incubation=[
                    BreedingIncubation(
                        duration=timedelta(seconds=incubation["duration"]),
                        enhanced=incubation["enhanced"],
                        skin_boost=incubation["skin_boost"],
                    )
                    for incubation in monster["breeding_incubation"]
                ],
                wiki_url=monster["wiki_url"],
            )
            for monster in self.bot.data["monsters"]
        ]

    def get_element_by_name(self, name: str) -> Optional[Element]:
        for element in self.elements:
            if element.name == name:
                return element
        return None

    def get_island_by_name(self, name: str) -> Optional[Island]:
        for island in self.islands:
            if island.name == name:
                return island
        return None

    def find_monster_by_breeding_time(
        self, duration: timedelta, enhanced: bool, skin_boost: bool
    ) -> List[Monster]:
        result = []
        for monster in self.monsters:
            for incubation in monster.breeding_incubation:
                if (
                    incubation.duration == duration
                    and incubation.enhanced == enhanced
                    and incubation.skin_boost == skin_boost
                ):
                    result.append(monster)
        return result

    def combine_elements(
        self, elements1: List[Element], elements2: List[Element]
    ) -> List[Element]:
        combined_elements = {element.name: element for element in elements1}
        for element in elements2:
            if element.name not in combined_elements:
                combined_elements[element.name] = element
        return list(combined_elements.values())

    def find_monster_by_elements(self, elements: List[Element]) -> List[Monster]:
        result = []
        for monster in self.monsters:
            if all(element in monster.elements for element in elements):
                result.append(monster)
        return result

    def parse_duration(self, duration_str: str) -> timedelta:
        parts = duration_str.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return timedelta(minutes=minutes, seconds=seconds)
        elif len(parts) == 1:
            seconds = int(parts[0])
            return timedelta(seconds=seconds)
        else:
            raise ValueError("Invalid duration format")

    async def get_bbb_id(self, interaction: Interaction, user: User) -> None:
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

        embed = Embed(
            title=f"Info for {user.mention}",
            description=description,
            color=0xBEBEFE,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)  # noqa

    @commands.hybrid_command(
        name="breeding_time",
        description="Find the monster based on breeding time and conditions.",
    )
    @app_commands.describe(
        duration="The breeding duration (format: HH:MM:SS or MM:SS or SS).",
        enhanced="Whether the breeding is enhanced.",
        skin_boost="Whether the breeding has a skin boost.",
    )
    @app_commands.choices(
        enhanced=[
            app_commands.Choice(name="Yes", value=1),
            app_commands.Choice(name="No", value=0),
        ],
        skin_boost=[
            app_commands.Choice(name="Yes", value=1),
            app_commands.Choice(name="No", value=0),
        ],
    )
    async def breeding_time(
        self, context: Context, duration: str, enhanced: int, skin_boost: int
    ) -> None:
        """
        Find the monster based on breeding time and conditions.

        :param context: The application command context.
        :param duration: The breeding duration (format: HH:MM:SS or MM:SS or SS).
        :param enhanced: Whether the breeding is enhanced.
        :param skin_boost: Whether the breeding has a skin boost.
        """
        try:
            breeding_duration = self.parse_duration(duration)
        except ValueError:
            embed = Embed(
                description="Invalid duration format. Please use HH:MM:SS, MM:SS, or SS.",
                color=0xE02B2B,
            )
            await context.send(
                embed=embed,
                ephemeral=True,
            )
            return

        monsters = self.find_monster_by_breeding_time(
            breeding_duration, bool(enhanced), bool(skin_boost)
        )
        if len(monsters) == 1:
            elements = ", ".join([element.name for element in monsters[0].elements])
            islands = ", ".join([island.name for island in monsters[0].islands])
            description = f"The matching monster bred with a duration of ({breeding_duration}), enhanced: {bool(enhanced)}, skin_boost: {bool(skin_boost)}: **[{monsters[0].name}]({monsters[0].wiki_url})**.\n\n**Elements:**\n{elements}\n\n**Islands:**\n{islands}"
        elif len(monsters) > 1:
            description = f"Multiple monsters match the criteria with a duration of ({breeding_duration}), enhanced: {bool(enhanced)}, skin_boost: {bool(skin_boost)}:\n"
            for monster in monsters:
                elements = ", ".join([element.name for element in monster.elements])
                islands = ", ".join([island.name for island in monster.islands])
                description += f"\n**[{monster.name}]({monster.wiki_url})**.\n\n**Elements:**\n{elements}\n\n**Islands:**\n{islands}"
        else:
            description = f"No monsters match the criteria with a duration of ({breeding_duration}), enhanced: {bool(enhanced)}, skin_boost: {bool(skin_boost)}."

        embed = Embed(
            title="Breeding Result",
            description=description,
            color=0xBEBEFE,
        )
        await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="breeding_combo",
        description="Determine the resulting monster based on breeding combination.",
    )
    @app_commands.describe(
        monster1="The name of the first monster.",
        monster2="The name of the second monster.",
    )
    async def breeding_combo(
        self, context: Context, monster1: str, monster2: str
    ) -> None:
        """
        Determine the resulting monster from two monsters.

        :param context: The application command context.
        :param monster1: The name of the first monster.
        :param monster2: The name of the second monster.
        """
        monster1_obj = next(
            (monster for monster in self.monsters if monster.name == monster1), None
        )
        monster2_obj = next(
            (monster for monster in self.monsters if monster.name == monster2), None
        )

        if not monster1_obj or not monster2_obj:
            description = "One or both monsters not found."
        else:
            combined_elements = self.combine_elements(
                monster1_obj.elements, monster2_obj.elements
            )
            resulting_monsters = self.find_monster_by_elements(combined_elements)
            if len(resulting_monsters) == 1:
                resulting_monster = resulting_monsters[0]
                elements = ", ".join([element.name for element in resulting_monster.elements])
                islands = ", ".join([island.name for island in resulting_monster.islands])
                breeding_times = "\n".join([f"Duration: {incubation.duration}, Enhanced: {incubation.enhanced}, Skin Boost: {incubation.skin_boost}" for incubation in resulting_monster.breeding_incubation])
                description = f"The resulting monster is **[{resulting_monster.name}]({resulting_monster.wiki_url})**.\n\n**Elements:**\n{elements}\n\n**Islands:**\n{islands}\n\n**Breeding/Incubation Times:**\n{breeding_times}"
            elif len(resulting_monsters) > 1:
                description = f"Multiple monsters match the criteria with {monster1_obj.name} and {monster2_obj.name}:\n"
                for monster in resulting_monsters:
                    elements = ", ".join([element.name for element in monster.elements])
                    breeding_times = "\n".join([f"Duration: {incubation.duration}, Enhanced: {incubation.enhanced}, Skin Boost: {incubation.skin_boost}" for incubation in monster.breeding_incubation])
                    description += f"\n**[{monster.name}]({monster.wiki_url})**\n\n**Elements:**\n{elements}\n\n**Breeding/Incubation Times:**\n{breeding_times}\n"
            else:
                description = f"No resulting monster matches the criteria with {monster1_obj.name} and {monster2_obj.name}."

        embed = Embed(
            title="Breeding Result",
            description=description,
            color=0xBEBEFE,
        )
        await context.send(embed=embed, ephemeral=True)

    @breeding_combo.autocomplete("monster1")
    @breeding_combo.autocomplete("monster2")
    async def autocomplete_monster(self, interaction: Interaction, current: str):
        choices = [app_commands.Choice(name=monster.name, value=monster.name) for monster in self.monsters if
                   current.lower() in monster.name.lower()]
        return choices

    @commands.hybrid_command(
        name="link",
        description="Link a BBB ID (friend code) to your Discord account.",
    )
    @app_commands.describe(
        bbb_id="The BBB ID to link.", bbb_name="The BBB name to link."
    )
    async def link(self, context: Context, bbb_id: str, bbb_name: str) -> None:
        """
        Link a BBB ID (friend code) to your Discord account.

        :param context: The application command context.
        :param bbb_id: The BBB ID to link.
        :param bbb_name: The BBB name to link.
        """
        success = await self.bot.database.set_bbb_id(
            context.author.id, bbb_id, bbb_name
        )
        if success:
            description = f"Successfully linked BBB ID `{bbb_id}` with name `{bbb_name}` to your account."
        else:
            description = (
                f"Failed to link BBB ID. It might already be linked to your account."
            )

        embed = Embed(
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
            description = (
                "Failed to unlink BBB ID. It might not be linked to your account."
            )

        embed = Embed(
            title="Link status",
            description=description,
            color=0xBEBEFE,
        )
        await context.send(embed=embed, ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(MySingingMonsters(bot))
