# PERSONAE


Personae is a tool for generating 5th edition Dungeons & Dragons characters. Currently, Personae supports content from the following rulebooks:

  * *Player's Handbook*
  * *Mordenkainen's Tome of Foes*
  * *Volo's Guide to Monsters*
  * *Xanathar's Guide to Everything*

TODO: Incorporate *Tasha's Cauldron of Everything*.


#### REQUIREMENTS

  * aiohttp
  * async-timeout
  * attrs
  * beautifulsoup4
  * chardet
  * colorama
  * idna
  * multidict
  * PyYAML
  * soupsieve
  * typing-extensions
  * yarl


#### INSTALLATION

To install, do the following:

```
$ git clone https://github.com/mtttech/dndpersonae.git

$ cd dndpersonae

$ python -m pip install -r requirements.txt
```


#### USAGE

Simply change into the newly cloned directory and type this command (following is an example of output from a running program and an explanation of all possible arguments follows this example):

```$ python personae -r Human -s Female -k Fighter```

Using the above example, here's an example program run.

```
$ python personae -r Human -s Female -k Fighter
[++] Personae is starting using the following options:
[+] Race: Human
[+] Sex: Female
[+] Class: Fighter
[+] Port: 5000
[PP] Choose your alignment:
[0] Chaotic Evil
[1] Chaotic Good
[2] Chaotic Neutral
[3] Lawful Evil
[4] Lawful Good
[5] Lawful Neutral
[6] Neutral Evil
[7] Neutral Good
[8] True Neutral
[**] 1
[N] Alignment set to >> Chaotic Good
[PP] Choose your background:
[0] Acolyte
[1] Charlatan
[2] Criminal
[3] Entertainer
[4] Folk Hero
[5] Guild Artisan
[6] Hermit
[7] Noble
[8] Outlander
[9] Sage
[10] Sailor
[11] Soldier
[12] Urchin
[**] 11
[N] Background set to >> Soldier
[PP] Choose your additional language:
[0] Abyssal
[1] Celestial
[2] Deep Speech
[3] Draconic
[4] Dwarvish
[5] Elvish
[6] Giant
[7] Gith
[8] Gnomish
[9] Goblin
[10] Halfling
[11] Infernal
[12] Orc
[13] Primordial
[14] Sylvan
[15] Undercommon
[**] 5
[N] Added language >> Elvish
[WW] Using a non-dominant gender height differential of -0".
[WW] Using a non-dominant gender weight differential of -0.15%.
[PP] Choose your class level:
[0] 1
[1] 2
[2] 3
[3] 4
[4] 5
[5] 6
[6] 7
[7] 8
[8] 9
[9] 10
[10] 11
[11] 12
[12] 13
[13] 14
[14] 15
[15] 16
[16] 17
[17] 18
[18] 19
[19] 20
[**] 3
[N] Level set to >> 4.
[PP] Choose a primary ability:
[0] Dexterity
[1] Strength
[**] 1
[N] Primary ability 'Strength' selected.
[PP] Choose a primary ability:
[0] Constitution
[1] Intelligence
[**] 0
[N] Primary ability 'Constitution' selected.
[PP] Choose class option 'skills' (2):
[0] Acrobatics
[1] Animal Handling
[2] Athletics
[3] History
[4] Insight
[5] Intimidation
[6] Perception
[7] Survival
[**] 1
[N] Value added >> Animal Handling.
[PP] Choose class option 'skills' (2):
[0] Acrobatics
[1] Athletics
[2] History
[3] Insight
[4] Intimidation
[5] Perception
[6] Survival
[**] 1
[N] Value added >> Athletics.
[PP] Choose class option 'subclass' (1):
[0] Arcane Archer
[1] Cavalier
[2] Champion
[3] Battle Master
[4] Eldritch Knight
[5] Samurai
[**] 2
[N] Value added >> Champion.
[N] Ability 'Strength' set to >> 17
[N] Ability 'Constitution' set to >> 16
[WW] Ability 'Charisma' set to >> 10
[WW] Ability 'Wisdom' set to >> 13
[WW] Ability 'Intelligence' set to >> 10
[WW] Ability 'Dexterity' set to >> 11
[N] Applied 1 bonus to 'Strength' (18).
[N] Applied 1 bonus to 'Dexterity' (12).
[N] Applied 1 bonus to 'Constitution' (17).
[N] Applied 1 bonus to 'Intelligence' (11).
[N] Applied 1 bonus to 'Wisdom' (14).
[N] Applied 1 bonus to 'Charisma' (11).
[N] You have 1 upgrade available.
[PP] Which path do you want to follow?
[0] Ability
[1] Feat
[**] 0
[PP] Do you want an upgrade of a +1 or +2?
[0] 1
[1] 2
[**] 1
[N] You may apply a +2 to one ability.
[PP] Which ability do you want to upgrade?
[0] Strength
[1] Dexterity
[2] Constitution
[3] Intelligence
[4] Wisdom
[5] Charisma
[**] 0
[N] Ability 'Strength' set to >> 20
[N] Upgraded ability >> Strength
======== Running on http://127.0.0.1:5000 ========
(Press CTRL+C to quit)
```

Now, a list of help options.

```
usage: personae [-h] -race
            {Aasimar,Bugbear,Dragonborn,Dwarf,Elf,Firbolg,Gith,Gnome,Goblin,Goliath,HalfElf,HalfOrc,Halfling,Hobgoblin,Human,Kenku,Kobold,Lizardfolk,Orc,Tabaxi,Tiefling,Triton,Yuanti}
            [-klass {Barbarian,Bard,Cleric,Druid,Fighter,Monk,Paladin,Ranger,Rogue,Sorcerer,Warlock,Wizard}]
            [-sex {Female,Male}] [-port PORT]

Generate 5th edition Dungeons & Dragons characters.

optional arguments:
  -h, --help            show this help message and exit
  -race {Aasimar,Bugbear,Dragonborn,Dwarf,Elf,Firbolg,Gith,Gnome,Goblin,Goliath,HalfElf,HalfOrc,Halfling,Hobgoblin,Human,Kenku,Kobold,Lizardfolk,Orc,Tabaxi,Tiefling,Triton,Yuanti}, -r {Aasimar,Bugbear,Dragonborn,Dwarf,Elf,Firbolg,Gith,Gnome,Goblin,Goliath,HalfElf,HalfOrc,Halfling,Hobgoblin,Human,Kenku,Kobold,Lizardfolk,Orc,Tabaxi,Tiefling,Triton,Yuanti}
                        sets character's race
  -klass {Barbarian,Bard,Cleric,Druid,Fighter,Monk,Paladin,Ranger,Rogue,Sorcerer,Warlock,Wizard}, -k {Barbarian,Bard,Cleric,Druid,Fighter,Monk,Paladin,Ranger,Rogue,Sorcerer,Warlock,Wizard}
                        sets character's class
  -sex {Female,Male}, -s {Female,Male}
                        sets character's sex
  -port PORT, -p PORT   sets HTTP server port
```


#### DISCLAIMER

This software is not affiliated with, endorsed, sponsored, or specifically approved
by Wizards of the Coast LLC. This software is a fan made tool.
