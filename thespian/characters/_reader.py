from ._loader import RulesetLoader


class RulesetReader:
    """Class to handle the retrieval of character rules."""

    def __init__(self):
        self.guidelines = dict()
        for guideline in RulesetLoader:
            self.guidelines[guideline.name] = guideline.value

    def _read_(self, category: str) -> dict | None:
        """Main getter wrapper."""
        try:
            return self.guidelines[category]
        except KeyError:
            return None

    @classmethod
    def get_all_alignments(cls) -> tuple:
        """Returns a tuple of all player character alignments."""
        getter = cls()
        return tuple(getter._read_("alignments"))

    @classmethod
    def get_all_backgrounds(cls) -> tuple:
        """Returns a tuple of all player character backgrounds."""
        getter = cls()
        return tuple(getter._read_("backgrounds").keys())

    @classmethod
    def get_all_classes(cls) -> tuple:
        """Returns a tuple of all player character classes."""
        getter = cls()
        return tuple(getter._read_("classes").keys())

    @classmethod
    def get_all_feats(cls) -> tuple:
        """Returns a tuple of all feats."""
        getter = cls()
        return tuple(getter._read_("feats").keys())

    @classmethod
    def get_all_races(cls) -> tuple:
        """Returns a tuple of all player character races."""
        getter = cls()
        return tuple(getter._read_("races").keys())

    @classmethod
    def get_all_skills(cls) -> tuple:
        """Returns a tuple of all skills."""
        getter = cls()
        return tuple(getter._read_("skills").keys())

    @classmethod
    def get_all_subclasses(cls, klass: str = None) -> tuple:
        """Returns a set of all player character subclasses."""
        getter = cls()
        try:
            return tuple(getter._read_("classes")[klass]["subclass"])
        except KeyError:
            return tuple(getter._read_("subclasses").keys())

    @classmethod
    def get_all_subraces(cls, race: str = None) -> tuple:
        """Returns a set of all player character subraces."""
        getter = cls()
        try:
            return tuple(getter._read_("races")[race]["subrace"])
        except KeyError:
            return tuple(getter._read_("subraces").keys())

    @classmethod
    def get_base_height(cls, race: str) -> str | None:
        """Returns base height values by race."""
        try:
            getter = cls()
            return getter._read_("metrics")[race]["height"]
        except KeyError:
            return None

    @classmethod
    def get_base_weight(cls, race: str) -> str | None:
        """Returns base weight values by race."""
        try:
            getter = cls()
            return getter._read_("metrics")[race]["weight"]
        except KeyError:
            return None

    @classmethod
    def get_dominant_sex(cls, race: str) -> str | None:
        """Returns the physically larger gender by race."""
        try:
            getter = cls()
            return getter._read_("metrics")[race]["dominant"]
        except KeyError:
            return None

    @classmethod
    def get_default_background(cls, klass: str) -> str | None:
        """Returns default background by class."""
        try:
            getter = cls()
            return getter._read_("classes")[klass]["background"]
        except KeyError:
            return None

    @classmethod
    def get_entry_background(cls, background: str) -> dict | None:
        """Returns config entry for background."""
        try:
            getter = cls()
            return getter._read_("backgrounds")[background]
        except KeyError:
            return None

    @classmethod
    def get_entry_class(cls, klass: str) -> dict | None:
        """Returns config entry for class."""
        try:
            getter = cls()
            return getter._read_("classes")[klass]
        except KeyError:
            return None

    @classmethod
    def get_entry_option_string(cls, category: str, entry: str) -> str | None:
        """Returns config entry for class."""
        try:
            getter = cls()
            return getter._read_(category)[entry]["_options"]
        except KeyError:
            return None

    @classmethod
    def get_entry_race(cls, race: str) -> dict | None:
        """Returns config entry for race."""
        try:
            getter = cls()
            return getter._read_("races")[race]
        except KeyError:
            return None

    @classmethod
    def get_entry_subclass(cls, subclass: str) -> dict | None:
        """Returns config entry for subclass."""
        try:
            getter = cls()
            return getter._read_("subclasses")[subclass]
        except KeyError:
            return None

    @classmethod
    def get_entry_subrace(cls, subrace: str) -> dict | None:
        """Returns config entry for subrace"""
        try:
            getter = cls()
            return getter._read_("subraces")[subrace]
        except KeyError:
            return None

    @classmethod
    def get_feat_perks(cls, feat_name: str) -> dict | None:
        """Returns perks by feat."""
        try:
            getter = cls()
            return getter._read_("feats")[feat_name]["perk"]
        except KeyError:
            return None

    @classmethod
    def get_feat_proficiencies(cls, feat: str, prof_type: str) -> list | None:
        """Returns bonus proficiencies by feat and proficiency type."""
        try:
            getter = cls()
            return getter._read_("feats")[feat]["perk"][prof_type]
        except KeyError:
            return None

    @classmethod
    def get_feat_requirements(cls, feat_name: str) -> dict | None:
        """Returns requirements by feat."""
        try:
            getter = cls()
            return getter._read_("feats")[feat_name]["required"]
        except KeyError:
            return None

    @classmethod
    def get_metrics_by_race(cls, race: str) -> str | None:
        """Returns metric data by race."""
        try:
            getter = cls()
            return getter._read_("metrics")[race]
        except KeyError:
            return None

    @classmethod
    def get_skill_ability(cls, skill_name: str) -> str | None:
        """Returns a skill's associated ability."""
        try:
            getter = cls()
            return getter._read_("skills")[skill_name]["associated_ability"]
        except KeyError:
            return None
