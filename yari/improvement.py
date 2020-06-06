from collections import OrderedDict
import random

from yari.collect import add, fuse, pick, purge
from yari.reader import reader
from yari.skills import get_all_skills


class ImprovementGenerator:
    """Handles leveled character's ability upgrades or additional feats.
        Chooses between a class ability or feat (where applicable)."""

    def __init__(
        self,
        race: str,
        klass: str,
        path: str,
        level: int,
        class_attr: dict,
        saves: list,
        spell_slots: str,
        score_array: OrderedDict,
        languages: list,
        armor_proficiency: list,
        tool_proficiency: list,
        weapon_proficiency: list,
        skills: list,
        variant: bool,
    ) -> None:
        """
        Args:
            race (str): Character's race.
            klass (str): Character's class.
            level (int): Character's level.
            class_attr (dict): Primary abilities for class_.
            saves (list): Character's proficient saving throws.
            spell_slots (str): Character's spell slots.
            score_array (OrderedDict): Character's ability scores.
            languages (list): Character's languages.
            armor_proficiency (list): Character's armor proficiencies.
            tool_proficiency (list): Character's tool proficiencies.
            weapon_proficiency (list): Character's weapon proficiencies.
            skills (list): Character's skills.
            variant (bool): Use variant rules.
        """
        self.klass = klass
        self.level = level
        self.saves = saves
        self.spell_slots = spell_slots
        self.score_array = score_array
        self.languages = languages
        self.armor_proficiency = armor_proficiency
        self.tool_proficiency = tool_proficiency
        self.weapon_proficiency = weapon_proficiency
        self.skills = skills
        self.feats = list()

        # Human and variant rules are used, give bonus feat.
        if race == "Human" and variant:
            self.add_feat()

        # Add special class languages (if applicable).
        if klass == "Druid":
            self.languages.append("Druidic")

        if klass == "Rogue":
            self.languages.append("Thieves' cant")
            # Assassins level 3 or higher, get bonus proficiencies.
            if path == "Assassin" and level >= 3:
                assassin_tools = reader("paths", (path, "proficiency", "tools"))
                fuse(self.tool_proficiency, assassin_tools)

        # Bards in the College of Lore get three bonus skills at level 3.
        if path == "College of Lore" and level >= 3:
            all_skills = get_all_skills()
            purge(all_skills, self.skills)
            fuse(self.skills, random.sample(all_skills, 3))

        # Determine number of applicable upgrades
        upgrades = 0
        for _ in range(1, level + 1):
            if (_ % 4) == 0 and _ is not 20:
                upgrades += 1

        if klass == "Fighter" and level >= 6:
            upgrades += 1

        if klass == "Rogue" and level >= 8:
            upgrades += 1

        if klass == "Fighter" and level >= 14:
            upgrades += 1

        if level >= 19:
            upgrades += 1

        # Cycle through the available upgrades (if applicable)
        if upgrades is 0:
            return

        class_attr = list(class_attr.values())
        for _ in range(1, upgrades):
            if len(class_attr) is 0:
                upgrade_option = "Feat"
            else:
                percentage = random.randint(1, 100)
                if percentage % 3:
                    upgrade_option = "Feat"
                elif percentage % 2:
                    upgrade_option = "Ability"
                else:
                    upgrade_option = "Feat"

            if upgrade_option == "Ability":
                try:
                    if len(class_attr) is 2:
                        if self.is_adjustable(class_attr):
                            for ability in class_attr:
                                self.set_score_array(ability, 1)
                                if not self.is_adjustable(ability):
                                    class_attr.remove(ability)
                        elif len(class_attr) is 1:
                            ability = class_attr[0]
                            if self.is_adjustable(ability):
                                self.set_score_array(ability, 2)
                                if not self.is_adjustable(ability):
                                    class_attr.remove(ability)
                        else:
                            raise ValueError
                    else:
                        raise ValueError
                except ValueError:
                    upgrade_option = "Feat"

            if upgrade_option == "Feat":
                self.feats.append(self.add_feat())

    def add_feat(self) -> str:
        """Randomly selects and adds a valid feats."""
        feats = list(reader("feats"))
        purge(feats, self.feats)

        # Keep choosing a feat until prerequisites are met.
        feat_choice = pick(feats)
        if not self.has_prerequisites(feat_choice):
            while not self.has_prerequisites(feat_choice):
                feat_choice = pick(feats)
        self.add_features(feat_choice)
        return feat_choice

    def add_features(self, feat: str) -> None:
        """Assign associated features by specified feat.
        
        Args:
            feat (str): Feat to add features for.
        """
        # Actor
        if feat == "Actor":
            self.set_score_array("Charisma", 1)

        # Athlete/Lightly Armored/Moderately Armored/Weapon Master
        if feat in (
            "Athlete",
            "Lightly Armored",
            "Moderately Armored",
            "Weapon Master",
        ):
            ability_choice = random.choice(["Strength", "Dexterity"])
            self.set_score_array(ability_choice, 1)
            if feat == "Lightly Armored":
                add(self.armor_proficiency, "Light")
            elif feat == "Moderately Armored":
                add(self.armor_proficiency, "Medium")
                add(self.armor_proficiency, "Shield")
        # Durable
        if feat == "Durable":
            self.set_score_array("Constitution", 1)

        # Heavily Armored/Heavy Armor Master
        if feat in ("Heavily Armored", "Heavy Armor Master"):
            self.set_score_array("Strength", 1)
            if feat == "Heavily Armored":
                add(self.armor_proficiency, "Heavy")

        # Keen Mind/Linguist
        if feat in ("Keen Mind", "Linguist"):
            self.set_score_array("Intelligence", 1)
            if feat == "Linguist":
                # Remove already known languages.
                linguist_languages = [
                    "Abyssal",
                    "Celestial",
                    "Common",
                    "Deep Speech",
                    "Draconic",
                    "Dwarvish",
                    "Elvish",
                    "Giant",
                    "Gnomish",
                    "Goblin",
                    "Halfling",
                    "Infernal",
                    "Orc",
                    "Primordial",
                    "Sylvan",
                    "Undercommon",
                ]
                purge(linguist_languages, self.languages)
                # Choose 3 bonus languages.
                fuse(self.languages, random.sample(linguist_languages, 3))

        # Observant
        if feat == "Observant":
            if self.klass in ("Cleric", "Druid"):
                self.set_score_array("Wisdom", 1)
            elif self.klass in ("Wizard",):
                self.set_score_array("Intelligence", 1)

        # Resilient
        if feat == "Resilient":
            # Remove all proficient saving throws.
            resilient_saves = [
                "Strength",
                "Dexterity",
                "Constitution",
                "Intelligence",
                "Wisdom",
                "Charisma",
            ]
            purge(resilient_saves, self.saves)
            # Choose one non-proficient saving throw.
            ability_choice = random.choice(resilient_saves)
            self.set_score_array(ability_choice, 1)
            add(self.saves, ability_choice)

        # Skilled
        if feat == "Skilled":
            for _ in range(3):
                skilled_choice = random.choice(["Skill", "Tool"])
                if skilled_choice == "Skill":
                    skills = purge(list(reader("skills")), self.skills)
                    add(self.skills, random.choice(skills))
                elif skilled_choice == "Tool":
                    tool_list = [t for t in self.get_tool_chest()]
                    purge(tool_list, self.tool_proficiency)
                    add(self.tool_proficiency, random.choice(tool_list))

        # Tavern Brawler
        if feat == "Tavern Brawler":
            self.set_score_array(random.choice(["Strength", "Constitution"]), 1)
            add(self.weapon_proficiency, "Improvised weapons")
            add(self.weapon_proficiency, "Unarmed strikes")

        # Weapon Master
        if feat == "Weapon Master":
            weapons = [t for t in self.get_weapon_chest()]
            selections = weapons[0]
            # Has Simple weapon proficiency.
            if "Simple" in self.weapon_proficiency:
                del selections["Simple"]
                selections = selections.get("Martial")
                # Has Simple and tight list of weapon proficiencies.
                if len(self.weapon_proficiency) > 1:
                    temp_proficiencies = list()
                    for proficiency in self.weapon_proficiency:
                        if proficiency != "Simple":
                            temp_proficiencies.append(proficiency)
                    purge(selections, temp_proficiencies)
                    temp_proficiencies.clear()
            # Doesn't have Simple or Martial proficiency but a tight list.
            elif "Simple" and "Martial" not in self.weapon_proficiency:
                selections = fuse(selections.get("Martial"), selections.get("Simple"))
                purge(selections, self.weapon_proficiency)

            fuse(self.weapon_proficiency, random.sample(selections, 4))
            selections.clear()

    @staticmethod
    def get_tool_chest():
        """Returns a full collection of tools."""
        for main_tool in reader("tools"):
            if main_tool in ("Artisan's tools", "Gaming set", "Musical instrument"):
                for sub_tool in reader("tools", (main_tool,)):
                    yield f"{main_tool} - {sub_tool}"
            else:
                yield main_tool

    @staticmethod
    def get_weapon_chest():
        """Returns a full collection of weapons."""
        weapon_chest = dict()
        for weapon_category in ("Simple", "Martial"):
            weapon_chest[weapon_category] = reader("weapons", (weapon_category,))
        yield weapon_chest

    def has_prerequisites(self, feat: str) -> bool:
        """Determines if character has the prerequisites for a feat.

        Args:
            feat (str): Feat to check prerequisites for.
        """
        if feat in self.feats:
            return False

        # If Heavily, Lightly, or Moderately Armored feat and a Monk.
        if (
            feat in ("Heavily Armored", "Lightly Armored", "Moderately Armored",)
            and self.klass == "Monk"
        ):
            return False
        # Chosen feat is "Armored" or Weapon Master but already proficient w/ assoc. armor type.
        elif feat in (
            "Heavily Armored",
            "Lightly Armored",
            "Moderately Armored",
            "Weapon Master",
        ):
            # Character already has heavy armor proficiency.
            if feat == "Heavily Armored" and "Heavy" in self.armor_proficiency:
                return False
            # Character already has light armor proficiency.
            elif feat == "Lightly Armored" and "Light" in self.armor_proficiency:
                return False
            # Character already has medium armor proficiency.
            elif feat == "Moderately Armored" and "Medium" in self.armor_proficiency:
                return False
            # Character already has martial weapon proficiency.
            elif feat == "Weapon Master" and "Martial" in self.weapon_proficiency:
                return False

        # Go through ALL additional prerequisites.
        prerequisite = reader("feats", (feat,))
        for requirement, _ in prerequisite.items():
            if requirement == "abilities":
                for ability, required_score in prerequisite.get("abilities").items():
                    my_score = self.score_array[ability]
                    if my_score < required_score:
                        return False

            if requirement == "caster":
                # Basic spell caster check, does the character have spells?
                if self.spell_slots == "":
                    return False

                # Magic Initiative
                if feat == "Magic Initiative" and self.klass not in (
                    "Bard",
                    "Cleric",
                    "Druid",
                    "Sorcerer",
                    "Warlock",
                    "Wizard",
                ):
                    return False

                # Ritual Caster
                if feat == "Ritual Caster":
                    my_score = 0
                    required_score = 0
                    if self.klass in ("Cleric", "Druid"):
                        my_score = self.score_array.get("Wisdom")
                        required_score = prerequisite.get("abilities").get("Wisdom")
                    elif self.klass == "Wizard":
                        my_score = self.score_array.get("Intelligence")
                        required_score = prerequisite.get("abilities").get(
                            "Intelligence"
                        )

                    if my_score < required_score:
                        return False
        return True

    def is_adjustable(self, abilities: (list, str)) -> (bool, int):
        """Determines if an ability can be adjusted i.e: not over 20.

        Args:
            abilities (list, str): skills to be checked.
        """
        if isinstance(abilities, list):
            for ability in abilities:
                value = self.score_array.get(ability)
                if (value + 1) > 20:
                    return False
        elif isinstance(abilities, str):
            for bonus in (2, 1):
                value = self.score_array.get(abilities)
                if (value + bonus) <= 20:
                    return bonus
            return False
        return True

    def set_score_array(self, ability: str, bonus: int) -> None:
        """Adjust a specified ability with bonus.

        Args:
            ability (str): Ability score to set.
            bonus (int): Value to apply to the ability score.
        """
        if not isinstance(self.score_array, OrderedDict):
            raise TypeError("argument 'score_array' must be 'OrderedDict' object")
        elif ability not in self.score_array:
            raise KeyError(f"not an available ability '{ability}'")
        else:
            value = self.score_array.get(ability) + bonus
            self.score_array[ability] = value
