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
  * termcolor
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
[+] Personae is starting using the following options:
[+] Race: Human
[+] Sex: Female
[+] Class: Fighter
[+] Port: 5000
[P] What is your alignment?
[0] Chaotic Evil
[1] Chaotic Good
[2] Chaotic Neutral
[3] Lawful Evil
[4] Lawful Good
[5] Lawful Neutral
[6] Neutral Evil
[7] Neutral Good
[8] True Neutral
[*] 3
[N] Alignment set to >> Lawful Evil
[P] What is your background?
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
[*] 4
[N] Background set to >> Folk Hero
[P] What additional language do you speak?
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
[*] 3
[N] Added language >> Draconic
[N] Using a non-dominant gender height differential of -3".
[N] Using a non-dominant gender weight differential of -0.19%.
[P] What level are you?
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
[*] 4
[N] Level set to >> 5.
[P] Choose a primary class ability:
[0] Dexterity
[1] Strength
[*] 0
[N] Class ability set to >> Dexterity
[P] Choose a primary class ability:
[0] Constitution
[1] Intelligence
[*] 0
[N] Class ability set to >> Constitution
[P] Choose class option 'skills' (2):
[0] Acrobatics
[1] Animal Handling
[2] Athletics
[3] History
[4] Insight
[5] Intimidation
[6] Perception
[7] Survival
[*] 4
[N] Value added >> Insight.
[P] Choose class option 'skills' (2):
[0] Acrobatics
[1] Animal Handling
[2] Athletics
[3] History
[4] Intimidation
[5] Perception
[6] Survival
[*] 3
[N] Value added >> History.
[P] Choose class option 'subclass' (1):
[0] Arcane Archer
[1] Cavalier
[2] Champion
[3] Battle Master
[4] Eldritch Knight
[5] Samurai
[*] 1
[N] Value added >> Cavalier.
[P] Choose a bonus 'skills' (1):
[0] Animal Handling
[1] History
[2] Insight
[3] Performance
[4] Persuasion
[*] 0
[N] Added 'skills' bonus >> Animal Handling.
[N] Ability 'Dexterity' set to >> 15
[N] Ability 'Constitution' set to >> 14
[N] Ability 'Wisdom' set to >> 14
[N] Ability 'Strength' set to >> 12
[N] Ability 'Charisma' set to >> 13
[N] Ability 'Intelligence' set to >> 9
[N] Applied 1 bonus to 'Strength' (13).
[N] Applied 1 bonus to 'Dexterity' (16).
[N] Applied 1 bonus to 'Constitution' (15).
[N] Applied 1 bonus to 'Intelligence' (10).
[N] Applied 1 bonus to 'Wisdom' (15).
[N] Applied 1 bonus to 'Charisma' (14).
[N] You have 1 upgrade available.
[P] Which path do you want to follow?
[0] Ability
[1] Feat
[*] 1
[P] Which feat do you want to acquire?
[0] Actor
[1] Alert
[2] Athlete
[3] Bountiful Luck
[4] Charger
[5] Crossbow Expert
[6] Defensive Duelist
[7] Dragon Fear
[8] Dragon Hide
[9] Drow High Magic
[10] Dual Wielder
[11] Dungeon Delver
[12] Durable
[13] Dwarven Fortitude
[14] Elemental Adept
[15] Elven Accuracy
[16] Fade Away
[17] Fey Teleportation
[18] Flames of Phlegethos
[19] Grappler
[20] Great Weapon Master
[21] Healer
[22] Heavily Armored
[23] Heavy Armor Master
[24] Infernal Constitution
[25] Inspiring Leader
[26] Keen Mind
[27] Lightly Armored
[28] Linguist
[29] Lucky
[30] Mage Slayer
[31] Magic Initiative
[32] Martial Adept
[33] Medium Armor Master
[34] Mobile
[35] Moderately Armored
[36] Mounted Combatant
[37] Observant
[38] Orcish Fury
[39] Polearm Master
[40] Prodigy
[41] Resilient
[42] Ritual Caster
[43] Savage Attacker
[44] Second Chance
[45] Sentinel
[46] Sharpshooter
[47] Shield Master
[48] Skilled
[49] Skulker
[50] Spell Sniper
[51] Squat Nimbleness
[52] Svirfneblin Magic
[53] Tavern Brawler
[54] Tough
[55] War Caster
[56] Weapon Master
[57] Wood Elf Magic
[*] 41
[N] Added feat >> Resilient
[P] Choose your bonus ability.
[0] Dexterity
[1] Intelligence
[2] Wisdom
[3] Charisma
[*] 1
[N] Added ability >> Intelligence
[N] Added saving throw proficiency >> Intelligence
[N] Ability 'Intelligence' set to >> 11
[N] Added feat >> Resilient
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
