import logging

from builder import _GuidelineBuilder
from notifications import prompt
from characters import RulesReader

log = logging.getLogger("thespian.parsers")


class FeatGuidelineParser(_GuidelineBuilder):
    """Class to handle feat guideline parsing."""

    def __init__(self, feat: str, character_base: dict):
        super(_GuidelineBuilder, self).__init__()
        self.feat = feat
        self.character_base = character_base

    def _get_perk_options(self, prof_type: str) -> list:
        """Returns a list of bonus proficiencies for a feat by proficiency type."""
        return RulesReader.get_feat_proficiencies(self.feat, prof_type)

    def parse(self) -> dict | None:
        """Creates guideline definitions from the raw guidelines based upon user's input (where applicable)."""
        # Gets the guideline definition string for the desired feat.
        feat_guidelines = RulesReader.get_entry_guide_string("feats", self.feat)

        # Forms the guideline string definition into a dictionary.
        raw_guidelines = self.build("feats", feat_guidelines)["feats"]

        # Check if definitions present, otherwise stop parsing.
        if len(raw_guidelines) == 0:
            return None

        # Used as a placeholder to store parsed definitions.
        feat_guidelines = dict()

        for guide_name, guide_options in raw_guidelines.items():
            guideline_increment = guide_options["increment"]
            if guideline_increment < 0:
                raise ValueError("Guideline 'increment' requires a positive value.")

            guideline_options = guide_options["options"]
            if len(guideline_options) < 1:
                raise ValueError("Guideline 'options' cannot be undefined.")

            if guide_name == "scores":
                if len(guideline_options) == 1:
                    my_ability = guideline_options[0]
                else:
                    # If 'savingthrows' guideline specified
                    # Add proficiency for ability saving throw.
                    if "savingthrows" not in raw_guidelines:
                        my_ability = prompt(
                            "Choose an attribute to upgrade.",
                            guideline_options,
                        )
                    else:
                        my_ability = prompt(
                            "Choose an attribute to upgrade.",
                            guideline_options,
                            self.character_base["savingthrows"],
                        )
                        feat_guidelines["savingthrows"].append(my_ability)
                feat_guidelines[guide_name] = {my_ability: guideline_increment}
            elif guide_name == "speed":
                feat_perks = RulesReader.get_feat_perks(self.feat)
                feat_guidelines[guide_name] = feat_perks[guide_name]
                continue

            if guide_name == "proficiency":
                # Get the type of proficiency bonus to apply.
                # Types: armors, languages, resistances, skills, tools, weapons
                proficiency_type = guideline_options[0]

                # Get a list of the applicable proficiency selection options.
                guideline_options = self._get_perk_options(proficiency_type)

                # Create special placeholder for user selection.
                feat_guidelines[proficiency_type] = []

                # Tuple options will be appended as is as a list.
                if isinstance(guideline_options, tuple) and guideline_increment == 0:
                    feat_guidelines[proficiency_type] = list(guideline_options)
                    continue

                # Non tuple options must have at least one option.
                # Otherwise, warn and ignore the guideline.
                if not isinstance(guideline_options, tuple) and guideline_increment < 1:
                    logging.warning(
                        "Invalid 'increment' parameter specified. Ignoring..."
                    )
                    continue

                # List/dict options allow the user to choose what to append.
                if isinstance(guideline_options, dict):
                    # Get the available proficiency groups.
                    selection_groups = tuple(guideline_options.keys())

                    # Create proficiency selection list from applicable groups.
                    proficiency_selections = []
                    for group in selection_groups:
                        if group not in self.character_base[proficiency_type]:
                            proficiency_selections += guideline_options[group]

                    # Replace guideline options with proficiency selections.
                    # Sort proficiency selections.
                    guideline_options = proficiency_selections
                    guideline_options.sort()

                for increment_count in range(guideline_increment):
                    my_bonus = prompt(
                        f"Choose your bonus: '{guide_name} >> {proficiency_type}' ({increment_count + 1}):",
                        guideline_options,
                        self.character_base[proficiency_type],
                    )

                    # Handle user's selections.
                    guideline_options.remove(my_bonus)
                    feat_guidelines[proficiency_type].append(my_bonus)
            elif guide_name == "spells":
                # Get a list of the applicable spell selection options.
                guideline_options = list(self._get_perk_options(guide_name))

                # Make spell selections where applicable.
                for index, spell in enumerate(guideline_options):
                    if not isinstance(spell, list):
                        continue

                    my_spell = prompt(
                        f"Choose your spell:",
                        spell,
                    )

                    # Handle user's spell selections
                    guideline_options[index] = my_spell

                # Sort the spell list alphabetically.
                guideline_options.sort()

                # Assign selected bonus spells.
                feat_guidelines[guide_name] = guideline_options

        return feat_guidelines

    def set(self, guidelines: dict) -> dict | None:
        """Applies feat perks to the character base."""
        if len(guidelines) == 0:
            return None

        for guideline, options in guidelines.items():
            if isinstance(options, tuple):
                options = list(options)

            if isinstance(options, dict):
                attributes = self.character_base[guideline]
                for attribute, bonus in options.items():
                    if attribute in attributes:
                        score = attributes[attribute] + bonus
                        attributes[attribute] = score

            if isinstance(options, list):
                # Amend to entries that already exist.
                # Create needed entries that don't yet exist.
                if guideline in self.character_base:
                    self.character_base[guideline] += options
                else:
                    self.character_base[guideline] = options

        return self.character_base
