from dataclasses import dataclass
from math import ceil, floor

from .sources import Load


@dataclass
class AttributeWriter:
    """Formats and prints attribute properties."""

    _ability: str
    _skills: list
    _value: int = 0

    def _get_attribute_array(self):
        """Generates attribute properties."""
        modifier = floor((self._value - 10) / 2)

        # All attributes have these properties.
        attr_array = dict()
        attr_array["ability_checks"] = modifier
        attr_array["saving_throws"] = modifier
        attr_array["value"] = self._value

        # Strength has three other unique properties.
        if self._ability == "Strength":
            attr_array["carry_capacity"] = self._value * 15
            attr_array["push_pull_carry"] = attr_array["carry_capacity"] * 2
            attr_array["maximum_lift"] = attr_array["push_pull_carry"]

        # Add any possessed skill associated with attribute in listing.
        attr_array["skills"] = list()
        for skill in self._skills:
            primary_ability = Load.get_columns(skill, "ability", source_file="skills")
            if primary_ability != self._ability:
                continue

            attr_array["skills"].append((skill, modifier))

        return attr_array

    @classmethod
    def write(cls, scores: dict, skills: list):
        attribs = dict()
        x = None
        for attribute in tuple(scores.keys()):
            x = cls(attribute, skills, scores.get(attribute))
            attribs[attribute] = x._get_attribute_array()

        block = ""
        for attribute, attributes in attribs.items():
            block += f"<h3>{attribute} ({attributes['value']})</h3>"
            block += "<ul>"
            for index, value in attributes.items():
                if index == "ability_checks":
                    block += f"<li>Ability Checks {value}</li>"
                if index == "saving_throws":
                    block += f"<li>Saving Throw Checks {value}</li>"
                if index == "carry_capacity":
                    block += f"<li>Carry Capacity {value}</li>"
                if index == "push_pull_carry":
                    block += f"<li>Push Pull Carry Capacity {value}</li>"
                if index == "maximum_lift":
                    block += f"<li>Maximum Lift Capacity {value}</li>"
                if index == "skills":
                    skill_list = attributes.get("skills")
                    if len(skill_list) != 0:
                        for pair in skill_list:
                            skill, modifier = pair
                            block += f"<li>{skill} Skill Checks {modifier}</li>"
            block += "</ul>"

        return block


@dataclass
class FeatureWriter:
    """Formats and prints class feature properties."""

    _features: dict

    def _format_features(self):
        for _, features in self._features.items():
            if type(features) is list:
                features.sort()

        return self._features

    @classmethod
    def write(cls, features: dict):
        x = cls(features)
        x._format_features()

        block = "<h2>CLASS FEATURES</h2>"

        block += "<p>"
        for level, features in x._features.items():
            for feature in features:
                block += f"{level}.) {feature}<br/>"
        block += "</p>"

        return block


@dataclass
class ListWriter:
    """Formats and prints custom list properties."""

    _header: str
    _items: list

    @classmethod
    def write(cls, header: str, items: list):
        x = cls(header, items)
        block = f"<h2>{x._header}</h2>"

        if len(x._items) != 0:
            x._items.sort()
            block += "<p>"
            for item in x._items:
                block += f"{item}<br/>"
            block += "</p>"
        else:
            block += "<p></p>"

        return block


class ProficiencyWriter:
    """Formats and print proficiency properties."""

    def __init__(
        self,
        armors,
        languages,
        level,
        saving_throws,
        scores,
        skills,
        speed,
        tools,
        weapons,
    ):
        self._armors = armors
        self._languages = languages
        self._proficiency_bonus = ceil((level / 4) + 1)
        self._saving_throws = saving_throws
        self._scores = scores
        self._skills = skills
        self._speed = speed
        self._tools = tools
        self._weapons = weapons

    def _sort_proficiencies(self):
        def organize_my_skills(my_skills):
            organized_skill_list = list()
            for skill in Load.get_columns(source_file="skills"):
                ability = Load.get_columns(skill, "ability", source_file="skills")
                if skill not in my_skills:
                    organized_skill_list.append((skill, ability, False))
                else:
                    organized_skill_list.append((skill, ability, True))
            return organized_skill_list

        for this_list in (
            self._armors,
            self._tools,
            self._weapons,
            self._languages,
            self._saving_throws,
            self._skills,
        ):
            this_list.sort()

        return {
            "armors": self._armors,
            "tools": self._tools,
            "weapons": self._weapons,
            "languages": self._languages,
            "saving_throws": self._saving_throws,
            "skills": organize_my_skills(self._skills),
        }

    @classmethod
    def write(
        cls,
        armors,
        languages,
        level,
        saving_throws,
        scores,
        skills,
        speed,
        tools,
        weapons,
    ):
        def get_modifier(value):
            return floor((value - 10) / 2)

        x = cls(
            armors,
            languages,
            level,
            saving_throws,
            scores,
            skills,
            speed,
            tools,
            weapons,
        )
        types = x._sort_proficiencies()

        block = "<h2>PROFICIENCIES</h2>"

        block += "<p>"
        block += f"<strong>Proficiency Bonus:</strong> {x._proficiency_bonus}<br/>"
        block += f"<strong>Initiative:</strong> {get_modifier(x._scores.get('Dexterity'))}<br/>"
        block += f"<strong>Speed:</strong> {x._speed}<br/>"
        block += "</p>"

        for object_type in (
            "armors",
            "tools",
            "weapons",
            "languages",
            "saving_throws",
            "skills",
        ):
            block += f"<h3>{object_type.capitalize()}</h3>"
            block += "<ul>"
            for obj in types.get(object_type):
                if object_type == "skills":
                    skill, ability, proficient = obj
                    base_modifier = get_modifier(x._scores.get(ability))

                    if proficient:
                        base_modifier += x._proficiency_bonus
                        block += f"<li><strong>{skill}</strong> {base_modifier} ({ability})</li>"
                    else:
                        block += f"<li>{skill} {base_modifier} ({ability})</li>"
                else:
                    block += f"<li>{obj}</li>"
            block += "</ul>"

        return block


@dataclass
class SpellWriter:
    """Formats and prints spell list properties."""

    _klass: str
    _level: int
    _spells: list

    @classmethod
    def write(cls, klass, level, spells):
        x = cls(klass, level, spells)
        block = ""
        if x._spells is None:
            return block

        extended_spells = list()
        for spell_level, spell_list in x._spells.items():
            if spell_level <= x._level:
                extended_spells += spell_list

        if klass in ("Cleric", "Druid", "Paladin", "Warlock"):
            if x._klass == "Cleric":
                title = "DOMAIN"
            elif x._klass == "Druid":
                title = "CIRCLE"
            elif x._klass == "Warlock":
                title = "EXPANDED"
            elif x._klass == "Paladin":
                title = "OATH"
            else:
                title = "EXTRA"
            block += f"<p><strong>{title} SPELLS</strong></p>"

            extended_spells.sort()
            block += "<p>"
            for spell in extended_spells:
                block += f"{spell}<br/>"
            block += "</p>"

        return block
