import logging

from builder import _RulesetGuidelineBuilder
from notifications import prompt
from characters import RulesetReader

log = logging.getLogger("thespian.parsers")


class FeatGuidelineBuilder(_RulesetGuidelineBuilder):
    def __init__(self, feat: str, character_base: dict):
        super(_RulesetGuidelineBuilder, self).__init__()
        self.feat = feat
        self.character_base = character_base

    def _get_bonus_proficiencies_by_type(self, proficiency_class: str) -> list:
        return RulesetReader.get_feat_proficiencies(self.feat, proficiency_class)

    def apply_perks(self, perks: dict) -> dict | None:
        try:
            if len(perks) == 0:
                raise TypeError
        except TypeError:
            return None

        for perk, options in perks.items():
            # Makes sure the options collection writeable.
            if isinstance(options, tuple):
                options = list(options)

            if isinstance(options, dict):
                attributes = self.character_base[perk]
                for attribute, bonus in options.items():
                    if attribute in attributes:
                        score = attributes[attribute] + bonus
                        attributes[attribute] = score

            if isinstance(options, list):
                # Amend to entries that already exist.
                # Create needed entries that don't yet exist.
                if perk in self.character_base:
                    self.character_base[perk] += options
                else:
                    self.character_base[perk] = options

        return self.character_base

    def build_guidelines(self) -> dict | None:
        # Gets the option string for the desired feat.
        options_string = RulesetReader.get_entry_option_string("feats", self.feat)

        # Converts the guideline string into a dictionary.
        # Returns None if no guideline string entry found.
        try:
            raw_guidelines = self.build_raw_guidelines("feats", options_string)["feats"]
        except TypeError:
            return None

        # Definitions present, but have no value.
        if len(raw_guidelines) == 0:
            return None

        # Used as a placeholder to store parsed definitions.
        feat_guidelines = dict()

        for guide_name, guide_options in raw_guidelines.items():
            increment = guide_options["increment"]
            if increment < 0:
                raise ValueError("Guideline 'increment' requires a positive value.")

            options = guide_options["options"]
            if len(options) < 1:
                raise ValueError("Guideline 'options' cannot be undefined.")

            if guide_name == "scores":
                if len(options) == 1:
                    my_ability = options[0]
                else:
                    # If 'savingthrows' guideline specified.
                    # Add proficiency for ability saving throw.
                    if "savingthrows" not in raw_guidelines:
                        my_ability = prompt(
                            "Choose an attribute to upgrade.",
                            options,
                        )
                    else:
                        my_ability = prompt(
                            "Choose an attribute to upgrade.",
                            options,
                            self.character_base["savingthrows"],
                        )
                        feat_guidelines["savingthrows"].append(my_ability)
                feat_guidelines[guide_name] = {my_ability: increment}
            elif guide_name == "speed":
                feat_perks = RulesetReader.get_feat_perks(self.feat)
                feat_guidelines[guide_name] = feat_perks[guide_name]
                continue

            if guide_name == "proficiency":
                # Get the type of proficiency bonus to apply.
                # Types: armors, languages, resistances, skills, tools, weapons
                proficiency_type = options[0]

                # Get a list of the applicable proficiency selection options.
                options = self._get_bonus_proficiencies_by_type(proficiency_type)

                # Create special placeholder for user selection.
                feat_guidelines[proficiency_type] = []

                # Tuple options will be appended as is as a list.
                if isinstance(options, tuple) and increment == 0:
                    feat_guidelines[proficiency_type] = list(options)
                    continue

                # Non tuple options must have at least one option.
                # Otherwise, warn and ignore the guideline.
                if not isinstance(options, tuple) and increment < 1:
                    logging.warning(
                        "Invalid 'increment' parameter specified. Ignoring..."
                    )
                    continue

                # List/dict options allow the user to choose what to append.
                if isinstance(options, dict):
                    # Get the available proficiency groups.
                    selection_groups = tuple(options.keys())

                    # Create proficiency selection list from applicable groups.
                    proficiency_selections = []
                    for group in selection_groups:
                        if group not in self.character_base[proficiency_type]:
                            proficiency_selections += options[group]

                    # Replace guideline options with proficiency selections.
                    # Sort proficiency selections.
                    options = proficiency_selections
                    options.sort()

                for increment_count in range(increment):
                    my_bonus = prompt(
                        f"Choose your bonus: '{guide_name} >> {proficiency_type}' ({increment_count + 1}):",
                        options,
                        self.character_base[proficiency_type],
                    )

                    # Handle user's selections.
                    options.remove(my_bonus)
                    feat_guidelines[proficiency_type].append(my_bonus)
            elif guide_name == "spells":
                # Get a list of the applicable spell selection options.
                options = list(self._get_bonus_proficiencies_by_type(guide_name))

                # Make spell selections where applicable.
                for index, spell in enumerate(options):
                    if not isinstance(spell, list):
                        continue

                    my_spell = prompt(
                        f"Choose your spell:",
                        spell,
                    )

                    # Handle user's spell selections
                    options[index] = my_spell

                # Sort the spell list alphabetically.
                options.sort()

                # Assign selected bonus spells.
                feat_guidelines[guide_name] = options

        return feat_guidelines
