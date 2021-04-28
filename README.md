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

```python yari -r=Tiefling -k=Rogue -l=6```


```
usage: Yari [-h] -race
            {Aasimar,Bugbear,Dragonborn,Dwarf,Elf,Firbolg,Gith,Gnome,Goblin,Goliath,HalfElf,HalfOrc,Halfling,Hobgoblin,Human,Kenku,Kobold,Lizardfolk,Orc,Tabaxi,Tiefling,Triton,Yuanti}
            [-subrace SUBRACE]
            [-klass {Barbarian,Bard,Cleric,Druid,Fighter,Monk,Paladin,Ranger,Rogue,Sorcerer,Warlock,Wizard}]
            [-subclass SUBCLASS]
            [-level {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20}]
            [-sex {Female,Male}]
            [-alignment {Chaotic Evil,Chaotic Good,Chaotic Neutral,Lawful Evil,Lawful Good,Lawful Neutral,Neutral Evil,Neutral Good,True Neutral}]
            [-background {Acolyte,Charlatan,Criminal,Entertainer,Folk Hero,Guild Artisan,Hermit,Noble,Outlander,Sage,Sailor,Soldier,Urchin}]
            [-port PORT]

Yari: A 5e Dungeons & Dragons character generator.

optional arguments:
  -h, --help            show this help message and exit
  -race {Aasimar,Bugbear,Dragonborn,Dwarf,Elf,Firbolg,Gith,Gnome,Goblin,Goliath,HalfElf,HalfOrc,Halfling,Hobgoblin,Human,Kenku,Kobold,Lizardfolk,Orc,Tabaxi,Tiefling,Triton,Yuanti}, -r {Aasimar,Bugbear,Dragonborn,Dwarf,Elf,Firbolg,Gith,Gnome,Goblin,Goliath,HalfElf,HalfOrc,Halfling,Hobgoblin,Human,Kenku,Kobold,Lizardfolk,Orc,Tabaxi,Tiefling,Triton,Yuanti}
                        sets character's race
  -subrace SUBRACE, -sr SUBRACE
                        sets character's subrace
  -klass {Barbarian,Bard,Cleric,Druid,Fighter,Monk,Paladin,Ranger,Rogue,Sorcerer,Warlock,Wizard}, -k {Barbarian,Bard,Cleric,Druid,Fighter,Monk,Paladin,Ranger,Rogue,Sorcerer,Warlock,Wizard}
                        sets character's class
  -subclass SUBCLASS, -sc SUBCLASS
                        sets character's subclass
  -level {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20}, -l {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20}
                        sets character's level
  -sex {Female,Male}, -s {Female,Male}
                        sets character's sex
  -alignment {Chaotic Evil,Chaotic Good,Chaotic Neutral,Lawful Evil,Lawful Good,Lawful Neutral,Neutral Evil,Neutral Good,True Neutral}, -a {Chaotic Evil,Chaotic Good,Chaotic Neutral,Lawful Evil,Lawful Good,Lawful Neutral,Neutral Evil,Neutral Good,True Neutral}
                        sets character's alignment
  -background {Acolyte,Charlatan,Criminal,Entertainer,Folk Hero,Guild Artisan,Hermit,Noble,Outlander,Sage,Sailor,Soldier,Urchin}, -b {Acolyte,Charlatan,Criminal,Entertainer,Folk Hero,Guild Artisan,Hermit,Noble,Outlander,Sage,Sailor,Soldier,Urchin}
                        sets character's background
  -port PORT, -p PORT   character's output HTTP server port
```


#### DISCLAIMER

This software is not affiliated with, endorsed, sponsored, or specifically approved
by Wizards of the Coast LLC. This software is a fan made tool.
