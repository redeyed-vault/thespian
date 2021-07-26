# Y.A.R.I - "Yet Another RPG Implement"


Yari is a tool for generating 5th edition Dungeons & Dragons characters. Currently, Yari supports content from the following rulebooks:

  * *Player's Handbook*
  * *Mordenkainen's Tome of Foes*
  * *Volo's Guide to Monsters*
  * *Xanatar's Guide to Everything*

Planning to eventually incorporate content from *Tasha's Cauldron of Everything*.


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

To use the 'testing' version of Yari, simply clone it:

```git clone -b testing https://github.com/taylormarcus/Yari.git```


#### USAGE

To run Yari, simply change into the cloned directory and type this command (a complete explanation of possible arguments follows this example):

```python yari -race Elf -klass Fighter -sex Female```


```
usage: Yari [-h] -race
            {Aasimar,Bugbear,Dragonborn,Dwarf,Elf,Firbolg,Gith,Gnome,Goblin,Goliath,HalfElf,HalfOrc,Halfling,Hobgoblin,Human,Kenku,Kobold,Lizardfolk,Orc,Tabaxi,Tiefling,Triton,Yuanti}
            [-klass {Barbarian,Bard,Cleric,Druid,Fighter,Monk,Paladin,Ranger,Rogue,Sorcerer,Warlock,Wizard}]
            [-sex {Female,Male}] [-port PORT]

A Dungeons & Dragons 5e character generator.

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
