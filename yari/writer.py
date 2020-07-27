from collections import OrderedDict
from datetime import datetime
import os

from bs4 import BeautifulSoup

from yari.attributes import (
    Charisma,
    Constitution,
    Dexterity,
    Intelligence,
    Strength,
    Wisdom,
)
from yari.version import __version__


class Writer:
    """Handles the authoring of the character sheet."""

    def __init__(self, data: OrderedDict) -> None:
        """
        Args:
            data (OrderedDict): Character's information packet.

        """
        save_path = os.path.expanduser("~/Yari")
        if not os.path.exists(save_path):
            os.mkdir(save_path)

        self.save_path = save_path

        if not isinstance(data, OrderedDict):
            raise TypeError("data argument must be of type 'OrderedDict'")

        data_keys = (
            "race",
            "subrace",
            "sex",
            "background",
            "size",
            "class",
            "level",
            "path",
            "bonus",
            "score_array",
            "saves",
            "proficiency",
            "languages",
            "spell_slots",
            "skills",
            "feats",
            "equipment",
            "features",
            "traits",
        )
        if not all(k in data for k in data_keys):
            raise ValueError("data: all keys must have a value!")
        else:
            self.data = data

    def __enter__(self):
        return self

    def __exit__(self, exec_type, value, traceback) -> None:
        pass

    def write(self, fp: str) -> None:
        """Writes data to character sheet in XML format.

        Args:
            fp (str): File to write character data to.

        """
        self.save_path = os.path.join(self.save_path, f"{fp}.xml")
        if os.path.exists(self.save_path):
            raise FileExistsError(f"character save '{self.save_path}' already exists.")

        now = datetime.now()
        timestamp = datetime.fromtimestamp(datetime.timestamp(now))

        if self.data.get("subrace") != "":
            race = f'{self.data.get("race")}, {self.data.get("subrace")}'
        else:
            race = self.data.get("race")

        score_array = self.data.get("score_array")
        strength = Strength(score_array.get("Strength"), self.data.get("skills"))
        dexterity = Dexterity(score_array.get("Dexterity"), self.data.get("skills"))
        constitution = Constitution(
            score_array.get("Constitution"), self.data.get("skills")
        )
        intelligence = Intelligence(
            score_array.get("Intelligence"), self.data.get("skills")
        )
        wisdom = Wisdom(score_array.get("Wisdom"), self.data.get("skills"))
        charisma = Charisma(score_array.get("Charisma"), self.data.get("skills"))

        x = '<?xml version="1.0"?><yari>'
        x += f"<meta><created>{timestamp}</created>"
        x += f"<version>{__version__}</version></meta>"
        x += f"<character><race>{race}</race>"
        x += f'<sex>{self.data.get("sex")}</sex>'
        x += f'<size>{self.data.get("size")}</size>'
        x += f'<background>{self.data.get("background")}</background>'
        x += f'<class>{self.data.get("class")}</class>'
        x += f'<level>{self.data.get("level")}</level>'
        x += f'<path>{self.data.get("path")}</path>'
        x += "<ability_scores>"
        x += format_ability(strength.attr)
        x += format_ability(dexterity.attr)
        x += format_ability(constitution.attr)
        x += format_ability(intelligence.attr)
        x += format_ability(wisdom.attr)
        x += format_ability(charisma.attr)
        x += "</ability_scores>"
        x += f'<spell_slots>{self.data.get("spell_slots")}</spell_slots>'
        x += "<proficiencies>"
        x += f'<proficiency>{self.data.get("bonus")}</proficiency>'
        x += format_proficiencies(self.data.get("proficiency"))
        x += f'<languages>{format_languages(self.data.get("languages"))}</languages>'
        x += "<saving_throws>"
        x += format_saving_throws(self.data.get("saves"))
        x += "</saving_throws><skills>"
        x += format_skills(self.data.get("skills"))
        x += "</skills></proficiencies><feats>"
        x += format_feats(self.data.get("feats"))
        x += "</feats><equipment>"
        x += format_equipment(self.data.get("equipment"))
        x += "</equipment><traits>"
        x += format_traits(self.data.get("traits"), race)
        x += "</traits><features>"
        x += format_features(self.data.get("class"), self.data.get("features"))
        x += "</features></character></yari>"
        x = BeautifulSoup(x, "xml").prettify()

        with open(self.save_path, "w+", encoding="utf-8") as cs:
            cs.write(x)
        cs.close()


def format_ability(attributes: dict):
    """Formats ability scores and associated ability check values.

    Args:
        attributes (dict): Ability to be formatted.

    """
    block = '<ability label="{}" value="{}">'.format(
        attributes.get("name"), attributes.get("value"),
    )
    for index, value in attributes.items():
        if index == "ability_checks":
            block += f'<entry label="Ability Checks" value="{value}"/>'
        if index == "saving_throws":
            block += f'<entry label="Saving Throw Checks" value="{value}"/>'
        if index == "skills":
            if len(value) is not 0:
                for skill, modifier in value.items():
                    block += f'<entry label="{skill} Skill Checks" value="{modifier}"/>'
        if index == "carry_capacity":
            block += f'<entry label="Carry Capacity" values="{value}"/>'
        if index == "push_pull_carry":
            block += f'<entry label="Push Pull Carry Capacity" values="{value}"/>'
        if index == "maximum_lift":
            block += f'<entry label="Maximum Lift Capacity" values="{value}"/>'
    block += "</{}>".format(attributes.get("name"))
    return block


def format_equipment(items: list) -> str:
    """Format equipment for character sheet.

    Args:
        items (list): Character's equipment list.

    """
    items.sort()
    block = ""
    for item in items:
        block += f'<entry label="equipment" value="{item}" />'
    return block


def format_feats(feats: list) -> str:
    """Formats feats for character sheet.

    Args:
        feats (list): Character's feat list.

    """
    feats.sort()
    block = ""
    for feat in feats:
        block += f'<entry label="feat" value="{feat}" />'
    return block


def format_features(klass: str, features: dict) -> str:
    """Formats class features for character sheet.

    Args:
        klass (str): Character's chosen class.
        features (dict): Character's class features.

    """
    block = ""
    for level, _features in features.items():
        for feature in _features:
            block += f'<entry label="{klass} Class Feature" level="{level}" name="{feature}" />'
    return block


def format_languages(languages: list) -> str:
    """Format languages for character sheet.

    Args:
        languages (list): Character's list of languages.

    """
    languages.sort()
    block = ""
    for language in languages:
        block += f'<entry label="language" value="{language}" />'
    return block


def format_proficiencies(proficiencies: OrderedDict) -> str:
    """Formats proficiencies for character sheet.

    Args:
        proficiencies (OrderedDict): OrderedDict of proficiency types/lists.

    """
    block = ""
    for type, proficiency_list in proficiencies.items():
        block += f"<{type}>"
        proficiency_list.sort()
        for proficiency in proficiency_list:
            block += f'<entry label="proficiency" value="{proficiency}" />'
        block += f"</{type}>"
    return block


def format_saving_throws(saves: list) -> str:
    """Formats proficient saves for character sheet.

    Args:
        saves (list): List of proficient saving throws.

    """
    saves.sort()
    block = ""
    for save in saves:
        block += '<entry label="save" value="%s" />' % save
    return block


def format_skills(skills: list) -> str:
    """Format skills for character sheet.

    Args:
        skills (list): Character's list of skills.

    """
    skills.sort()
    block = ""
    for skill in skills:
        block += f'<entry label="skill" value="{skill}" />'
    return block


def format_traits(traits: list, race: str) -> str:
    """Formats trait values for character sheet.

    Args:
        traits (list): Character's racial traits.
        race (str): Character's chosen race.

    """
    block = ""
    for trait in traits:
        if len(trait) > 1:
            (name, value) = trait
            if isinstance(value, list):
                if (
                    name == "Drow Magic"
                    or name.startswith("Legacy of")
                ):
                    value = [v[1] for v in value]
                value = ", ".join(value)
            block += f'<entry label="{race} Trait" name="{name}" value="{value}" />'
        else:
            block += f'<entry label="{race} Trait" name="{trait[0]}" />'
    return block
