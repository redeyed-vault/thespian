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


#### DISCLAIMER

This software is not affiliated with, endorsed, sponsored, or specifically approved
by Wizards of the Coast LLC. This software is a fan made tool.
