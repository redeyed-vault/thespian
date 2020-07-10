# YARI: "Yet Another RPG Implement"


#### DESCRIPTION

My tool for making quick and easy 5th edition Dungeons & Dragons characters.

Originally this project was known as personaednd and dndpersona.

"Yari is the term for a traditionally-made Japanese blade in the form of a spear, or more specifically, the straight-headed spear."
 - From Wikipedia, the free encyclopedia - http://www.wikipedia.org

#### DISCLAIMER

This software is not affiliated with, endorsed, sponsored, or specifically approved
by Wizards of the Coast LLC. This software is a fan made tool.


#### REQUIREMENTS

  * beautifulsoup4
  * click
  * lxml
  * PyYAML


#### INSTALLATION

To install Yari from source, clone the repository and run the setup script:

```python setup.py install``` or ```python3 setup.py install```

To install Yari from PYPI, run the following command:

```pip install Yari``` or ```pip3 install Yari```


#### USAGE

```
Usage: yari [OPTIONS]

Options:
  -file TEXT         Character output file name.  [required]
  -race TEXT         Character's chosen race.
  -subrace TEXT      Character's chosen subrace.
  -sex TEXT          Character's chosen gender.
  -background TEXT   Character's chosen background.
  -klass TEXT        Character's chosen class.
  -path TEXT         Character's chosen path (archetype, domain, path, etc).
  -level INTEGER     Character's class level.
  -variant TEXT      Use variant rules (Humans only).
  --version          Show the version and exit.
  --help             Show this message and exit.
```

To run Yari with minimal arguments, type the following in your terminal:

    yari -file=some_character_file

If run with just the bare minimum arguments as shown above, Yari will randomly generate the character's race, subrace, sex, klass and path. Level will be defaulted to 1 and the background defaults to the default for the chosen klass.

Character's will always be saved to *$HOME/Yari*.

Valid argument parameters:

**-race**

    Aasimar
    Dragonborn
    Dwarf
    Elf
    Gith
    Gnome
    HalfElf
    HalfOrc
    Halfling
    Human
    Tiefling

**-subrace** (*valid subrace parameters are dependent on the chosen -race parameter*)

    -race=Aasimar
        Fallen
        Protector
        Scourge
        
    -race=Dwarf
        Duergar
        Hill
        Mountain

    -race=Elf
        Drow
        Eladrin
        High
        Sea
        Shadar-kai
        Wood
        
    -race=Gith
        Githyanki
        Githzerai

    -race=Gnome
        Deep
        Forest
        Rock

    -race=Halfling
        Lightfoot
        Stout

**Note that Dragonborn, HalfElf, HalfOrc, Human, and Tiefling characters have no valid subrace options currently implemented within this application.*

**-sex**

    Female
    Male

**-background**

    Acolyte
    Charlatan
    Criminal
    Entertainer
    Folk Hero
    Guild Artisan
    Hermit
    Noble
    Outlander
    Sage
    Sailor
    Soldier
    Urchin

**-klass**

    Barbarian
    Bard
    Cleric
    Druid
    Fighter
    Monk
    Paladin
    Ranger
    Rogue
    Sorcerer
    Warlock
    Wizard

**-path** (**valid path parameters are dependent on the chosen -klass parameter*)

    -klass=Barbarian
        Path of the Beserker
        Path of the Totem Warrior

    -klass=Bard
        College of Lore
        College of Valor

    -klass=Cleric
        Knowledge Domain
        Life Domain
        Light Domain
        Nature Domain
        Tempest Domain
        Trickery Domain
        War Domain

    -klass=Druid
        Circle of the Artic
        Circle of the Coast
        Circle of the Desert
        Circle of the Forest
        Circle of the Grassland
        Circle of the Moon
        Circle of the Mountain
        Circle of the Swamp
        Circle of the Underdark

    -klass=Fighter
        Battle Master
        Champion
        Eldritch Knight

    -klass=Monk
        Way of Shadow
        Way of the Four Elements
        Way of the Open Hand

    -klass=Paladin
        Oath of the Ancients
        Oath of Devotion
        Oath of Vengeance

    -klass=Ranger
        Beast Master
        Hunter

    -klass=Rogue
        Arcane Trickster
        Assassin
        Thief

    -klass=Sorcerer
        Draconic Bloodline
        Wild Magic

    -klass=Warlock
        The Archfey
        The Fiend
        The Great Old One

    -klass=Wizard
        School of Abjuration
        School of Conjuration
        School of Divination
        School of Enchantment
        School of Evocation
        School of Illusion
        School of Necromancy
        School of Transmutation

**-level**

    1-20

**-variant**

    false
    true

**Note that the variant argument is only used by Human characters and is automatically set to "false" for non-humans.*
