# Y.A.R.I - "Yet Another RPG Implement"


> "Yari is the term for a traditionally-made Japanese blade in the form of a spear, or more specifically, the straight-headed spear. - From [Wikipedia](http://www.wikipedia.org), the free encyclopedia


#### DESCRIPTION

Yari generates quick and easy 5th edition Dungeons & Dragons characters. Currently the software supports content from the following rulebooks: *Player's Handbook*, *Volo's Guide to Monsters* and *Xanatar's Guide to Everything* (partially).

This project was originally known as *personaednd* and later *dndpersona*.


#### REQUIREMENTS
  
  * aiohttp ~= 3.6.2
  * beautifulsoup4 ~= 4.9.1
  * click ~= 7.1.2
  * lxml ~= 4.5.2
  * PyYAML ~= 5.3.1


#### INSTALLATION

To install Yari directly from Github (usually the latest version):

```pip install git+git://github.com/taylormarcus/Yari``` or ```pip3 install git+git://github.com/taylormarcus/Yari```

To install Yari from PYPI, run the following command:

```pip install Yari``` or ```pip3 install Yari```


#### USAGE

```
Usage: yari [OPTIONS]

Options:
  -race TEXT        Character's chosen race. Available races are: Aasimar,
                    Bugbear, Dragonborn, Dwarf, Elf, Firbolg, Gith, Gnome,
                    Goblin, Goliath, HalfElf, HalfOrc, Halfling, Hobgoblin,
                    Human, Kenku, Kobold, Lizardfolk, Orc, Tabaxi, Tiefling,
                    Triton and Yuanti. Default value is 'Human'.

  -subrace TEXT     Character's chosen subrace. Available subraces are based
                    upon the chosen race: Aasimar (Fallen, Protector,
                    Scourge), Dwarf (Duergar, Hill, Mountain), Elf (Drow,
                    Eladrin, High, Sea, Shadar-kai, Wood), Gith (Githyanki,
                    Githzerai), Gnome (Deep, Forest, Rock), Halfling
                    (Lightfoot, Stout), Tiefling (Asmodeus, Baalzebub,
                    Dispater, Fierna, Glasya, Levistus, Mammon,
                    Mephistopheles, Zariel).

  -sex TEXT         Character's chosen gender.
  -alignment TEXT   Character's chosen alignment. Available alignments are:
                    CE, CG, CN, LE, LG, LN, NE, NG, N. Default value is 'N'.

  -background TEXT  Character's chosen background. Available backgrounds are:
                    Acolyte, Charlatan, Criminal, Entertainer, Folk Hero,
                    Guild Artisan, Hermit, Noble, Outlander, Sage, Sailor,
                    Soldier, Urchin.

  -klass TEXT       Character's chosen class. Available classes are:
                    Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin,
                    Ranger, Rogue, Sorcerer, Warlock, and Wizard. Default
                    value is 'Fighter'.

  -subclass TEXT    Character's chosen subclass (archetype, domain, path,
                    etc). Available subclasses are based upon the chosen
                    class: Barbarian (Path of the Berserker, Path of the Totem
                    Warrior), Bard (College of Lore, College of Valor), Cleric
                    (Knowledge Domain, Life Domain, Light Domain, Nature
                    Domain, Tempest Domain, Trickery Domain, War Domain),
                    Druid (Circle of the Arctic, Circle of the Coast, Circle
                    of the Desert, Circle of the Forest, Circle of the
                    Grassland, Circle of the Moon, Circle of the Mountain,
                    Circle of the Swamp, Circle of the Underdark), Fighter
                    (Battle Master, Champion, Eldritch Knight), Monk (Way of
                    Shadow, Way of the Four Elements, Way of the Open Hand),
                    Paladin (Oath of the Ancients, Oath of Devotion, Oath of
                    Vengeance), Ranger (Beast Master, Hunter), Rogue (Arcane
                    Trickster, Assassin, Thief), Sorcerer (Draconic Bloodline,
                    Wild Magic), Warlock (The Archfey, The Fiend, The Great
                    Old One), and Wizard (School of Abjuration, School of
                    Conjuration, School of Divination, School of Enchantment,
                    School of Evocation, School of Illusion, School of
                    Necromancy, School of Transmutation).

  -level INTEGER    Character's class level. Must be between 1-20. Default
                    value is 1.

  -ratio INTEGER    Character's 'ability to feat' upgrade ratio. Must be
                    between 0-10. This value will determine the percentage of
                    level upgrades allocated to the character's ability
                    scores. The difference between this value from 100 will
                    then be allocated to the percentage of chosen feats (i.e:
                    So if this value is 2 or 20%, 80 percent will
                    automatically be allocated to feats). Default value is 5.

  -port INTEGER     Character server's chosen port. Default value is 8080.
  --version         Show the version and exit.
  --help            Show this message and exit.
```

To run Yari with minimal arguments, type the following in your terminal:

    yari

If Yari is run with just the bare minimum arguments as shown above, a character will be generated using the previously mentioned default values where applicable and randomly generate those values that have no defined default values.


#### DISCLAIMER

This software is not affiliated with, endorsed, sponsored, or specifically approved
by Wizards of the Coast LLC. This software is a fan made tool.
