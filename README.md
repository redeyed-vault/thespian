# YARI: "Yet Another RPG Implement"


#### DESCRIPTION

My tool for making quick and easy 5th edition Dungeons & Dragons characters.

Originally this project was known as *personaednd* and *dndpersona*.

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
  -file TEXT        File name to write character to.  [required]
  -race TEXT        Character's chosen race. Available races are: Aasimar,
                    Dragonborn, Dwarf, Elf, Gith, Gnome, HalfElf, HalfOrc,
                    Halfling, Human and Tiefling.

  -subrace TEXT     Character's chosen subrace. Available subraces are based
                    upon the chosen race: Aasimar (Fallen, Protector,
                    Scourge), Dwarf (Duergar, Hill, Mountain), Elf (Drow,
                    Eladrin, High, Sea, Shadar-kai, Wood), Gith (Githyanki,
                    Githzerai), Gnome (Deep, Forest, Rock), Halfling
                    (Lightfoot, Stout).

  -sex TEXT         Character's chosen gender.
  -background TEXT  Character's chosen background. Available backgrounds are:
                    Acolyte, Charlatan, Criminal, Entertainer, Folk Hero,
                    Guild Artisan, Hermit, Noble, Outlander, Sage, Sailor,
                    Soldier, Urchin

  -klass TEXT       Character's chosen class. Available classes are:
                    Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin,
                    Ranger, Rogue, Sorcerer, Warlock, and Wizard.

  -path TEXT        Character's chosen path (archetype, domain, path, etc).
                    Available paths are based upon the chosen class: Barbarian
                    (Path of the Berserker, Path of the Totem Warrior), Bard
                    (College of Lore, College of Valor), Cleric (Knowledge
                    Domain, Life Domain, Light Domain, Nature Domain, Tempest
                    Domain, Trickery Domain, War Domain), Druid (Circle of the
                    Arctic, Circle of the Coast, Circle of the Desert, Circle
                    of the Forest, Circle of the Grassland, Circle of the
                    Moon, Circle of the Mountain, Circle of the Swamp, Circle
                    of the Underdark), Fighter (Battle Master, Champion,
                    Eldritch Knight), Monk (Way of Shadow, Way of the Four
                    Elements, Way of the Open Hand), Paladin (Oath of the
                    Ancients, Oath of Devotion, Oath of Vengeance), Ranger
                    (Beast Master, Hunter), Rogue (Arcane Trickster, Assassin,
                    Thief), Sorcerer (Draconic Bloodline, Wild Magic), Warlock
                    (The Archfey, The Fiend, The Great Old One), and Wizard
                    (School of Abjuration, School of Conjuration, School of
                    Divination, School of Enchantment, School of Evocation,
                    School of Illusion, School of Necromancy, School of
                    Transmutation).

  -level INTEGER    Character's class level. Must be at or inbetween 1 and 20.
  -variant TEXT     Use variant rules (Humans only).
  --version         Show the version and exit.
  --help            Show this message and exit.
```

To run Yari with minimal arguments, type the following in your terminal:

    yari -file=some_character_file

If run with just the bare minimum arguments as shown above, Yari will randomly generate the character's race, subrace, sex, class and path. Level will be defaulted to 1 and the background defaults to the default for the chosen class.

Generated characters will always be saved to the directory *$HOME/Yari*.
