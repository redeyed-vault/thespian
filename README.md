# PERSONAE


Personae is a tool for generating 5th edition Dungeons & Dragons characters. Currently, Personae supports content from the following rulebooks:

  * *Player's Handbook*
  * *Mordenkainen's Tome of Foes*
  * *Volo's Guide to Monsters*
  * *Xanatar's Guide to Everything*

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

Simply change into the cloned directory and type this command (a complete explanation of possible arguments follows this example):

```$ python personae -r Elf -k Fighter -s Female```


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

The following is an example of output given during a normal run of the program.

```
$ python personae -s Female -r Human
What is your chosen alignment?

	0.) Chaotic Evil
	1.) Chaotic Good
	2.) Chaotic Neutral
	3.) Lawful Evil
	4.) Lawful Good
	5.) Lawful Neutral
	6.) Neutral Evil
	7.) Neutral Good
	8.) True Neutral

Enter a number >> 2
INFO: You set your alignment to > Chaotic Neutral.
What is your background?

	0.) Acolyte
	1.) Charlatan
	2.) Criminal
	3.) Entertainer
	4.) Folk Hero
	5.) Guild Artisan
	6.) Hermit
	7.) Noble
	8.) Outlander
	9.) Sage
	10.) Sailor
	11.) Soldier
	12.) Urchin

Enter a number >> 11
INFO: Character background 'Soldier' chosen.
What additional language do you want?

	0.) Abyssal
	1.) Celestial
	2.) Deep Speech
	3.) Draconic
	4.) Dwarvish
	5.) Elvish
	6.) Giant
	7.) Gith
	8.) Gnomish
	9.) Goblin
	10.) Halfling
	11.) Infernal
	12.) Orc
	13.) Primordial
	14.) Sylvan
	15.) Undercommon

Enter a number >> 4
INFO: Character language 'Dwarvish' chosen.
INFO: Using a non-dominant gender height differential of -0".
INFO: Using a non-dominant gender weight differential of -0.19%.
What level are you?

	0.) 1
	1.) 2
	2.) 3
	3.) 4
	4.) 5
	5.) 6
	6.) 7
	7.) 8
	8.) 9
	9.) 10
	10.) 11
	11.) 12
	12.) 13
	13.) 14
	14.) 15
	15.) 16
	16.) 17
	17.) 18
	18.) 19
	19.) 20

Enter a number >> 1
INFO: Your character level has been set to 2.
Choose class option 'ability':

	0.) Dexterity
	1.) Strength

Enter a number >> 1
You chose the ability > 'Strength'
Choose class option 'ability':

	0.) Constitution
	1.) Intelligence

Enter a number >> 1
You chose the ability > 'Intelligence'
Choose class option 'skills' (2):

	0.) Acrobatics
	1.) Animal Handling
	2.) Athletics
	3.) History
	4.) Insight
	5.) Intimidation
	6.) Perception
	7.) Survival

Enter a number >> 2
INFO: You chose > Athletics.
Choose class option 'skills' (2):

	0.) Acrobatics
	1.) Animal Handling
	2.) History
	3.) Insight
	4.) Intimidation
	5.) Perception
	6.) Survival

Enter a number >> 0
INFO: You chose > Acrobatics.
INFO: Ability 'Strength' set to 18.
INFO: Ability 'Intelligence' set to 11.
INFO: Ability 'Charisma' set to 11.
INFO: Ability 'Constitution' set to 8.
INFO: Ability 'Dexterity' set to 11.
INFO: Ability 'Wisdom' set to 9.
INFO: Bonus of 1 applied to 'Strength' (19).
INFO: Bonus of 1 applied to 'Dexterity' (12).
INFO: Bonus of 1 applied to 'Constitution' (9).
INFO: Bonus of 1 applied to 'Intelligence' (12).
INFO: Bonus of 1 applied to 'Wisdom' (10).
INFO: Bonus of 1 applied to 'Charisma' (12).
======== Running on http://127.0.0.1:5000 ========
(Press CTRL+C to quit)
```

#### DISCLAIMER

This software is not affiliated with, endorsed, sponsored, or specifically approved
by Wizards of the Coast LLC. This software is a fan made tool.
