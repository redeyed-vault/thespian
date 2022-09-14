class _OptionsBuilder:
    """Class base that builds guideline instructions from strings.

    ===================================
    # SEPARATOR DESCRIPTIONS
    ===================================

    SEMICOLON: Used to separate flags. i.e: ability=Strength;proficiency=skills
        Two flag options are designated in the above example: 'ability', and 'proficiency'.

    EQUAL SIGN: Used to separate option parameters. i.e ability=Strength,1
        The example above means Strength is a designated parameter for the ability flag.
        In this case the character would get an enhancement to Strength.
        There is more to this and is explained further below.

    COMMA: Used to set a parameter's number of applications. i.e: languages,2
        The example above means that a player can choose two languages.

    DOUBLE AMPERSAND: Used to seperate parameter options. i.e ability=Strength&&Dexterity,1
        The example above means the player can gain an enhancement in both Strength and Dexterity.

    DOUBLE PIPEBAR: Used to separater parameter options. i.e ability=Strength||Dexerity,1
        The example above means the player can choose a one time ehancement to Strength or Dexterity.

    """

    SEPARATOR_CHARS = (";", "=", ",", "&&", "||")

    @classmethod
    def build(cls, build_name: str, option_string: str) -> dict | None:
        """Translates rule strings into guideline instructions."""
        if option_string is None:
            return None

        # Init
        super(_OptionsBuilder, cls).__init__(option_string)

        # Stores guidelines.
        guidelines = dict()

        # Separate flag string into raw pair strings. CHAR: ";"
        guideline_pairs = option_string.split(cls.SEPARATOR_CHARS[0])

        separator_ampersand = cls.SEPARATOR_CHARS[3]
        separator_comma = cls.SEPARATOR_CHARS[2]
        separator_equalsign = cls.SEPARATOR_CHARS[1]
        separator_pipes = cls.SEPARATOR_CHARS[4]

        # Cycle through raw string pairs.
        for guideline_pair in guideline_pairs:
            # Checks if "pair" is formatted to be splitted. CHAR ","
            if separator_comma not in guideline_pair:
                raise ValueError("Pairs must be formatted in 'name,value' pairs.")

            # Split pair into flag_name/flag_increment.
            guide_name, guide_increment = guideline_pair.split(separator_comma)

            # Check if flag_name has no equal sign character. CHAR "="
            if separator_equalsign not in guide_name:
                guidelines[guide_name] = {"increment": int(guide_increment)}
            else:
                guide_options = guide_name.split(separator_equalsign)
                guide_name = guide_options[0]

                # If double ampersand, save options as tuple
                # If double pipes, save options as list
                # If neither, encase option in list
                if separator_ampersand in guide_options[1]:
                    guide_options = tuple(guide_options[1].split(separator_ampersand))
                elif separator_pipes in guide_options[1]:
                    guide_options = guide_options[1].split(separator_pipes)
                else:
                    guide_options = [guide_options[1]]

                # Apply the guidelines.
                guidelines[guide_name] = {
                    "increment": int(guide_increment),
                    "options": guide_options,
                }

        return {build_name: guidelines}
