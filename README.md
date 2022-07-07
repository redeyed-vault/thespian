# THESPIAN (T22)


Thespian is a tool for generating 5th edition Dungeons & Dragons characters. Currently, Thespian supports content from the following rulebooks:

  * *Player's Handbook*
  * *Mordenkainen's Tome of Foes*
  * *Volo's Guide to Monsters*
  * *Xanathar's Guide to Everything*
  * *Tasha's Cauldron of Everything*

##### Future Goals (TODO List)

  * Work out ALL general bugs/inconsistencies before moving forward.
  * Incorporate *Sword Coast Adventurer's Guide* rulebook.


#### REQUIREMENTS

  * colorama
  * flask


#### INSTALLATION

To install, do the following:

```
$ git clone https://github.com/mtttech/thespian.git

$ cd src/thespian

$ python -m pip install -r requirements.txt
```


#### USAGE

```
$ python src/thespian -h
usage: thespian (VERSION) [-h]
                [-race {Aasimar,Bugbear,Dragonborn,Dwarf,Elf,Firbolg,Gith,Gnome,Goblin,Goliath,HalfElf,HalfOrc,Halfling,Hobgoblin,Human,Kenku,Kobold,Lizardfolk,Orc,Tabaxi,Tiefling,Triton,Yuanti}]
                [-subrace SUBRACE]
                [-sex {Female,Male}]
                [-background {Acolyte,Charlatan,Criminal,Entertainer,Folk Hero,Guild Artisan,Hermit,Noble,Outlander,Sage,Sailor,Soldier,Urchin}]
                [-klass {Barbarian,Bard,Cleric,Druid,Fighter,Monk,Paladin,Ranger,Rogue,Sorcerer,Warlock,Wizard}]
                [-subclass SUBCLASS]
                [-level {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20}]
                [-threshold THRESHOLD] [-port PORT] [--roll-hp]

Generate 5th edition Dungeons & Dragons characters.   

options:
  -h, --help            show this help message and    
                        exit
  -race {Aasimar,Bugbear,Dragonborn,Dwarf,Elf,Firbolg,Gith,Gnome,Goblin,Goliath,HalfElf,HalfOrc,Halfling,Hobgoblin,Human,Kenku,Kobold,Lizardfolk,Orc,Tabaxi,Tiefling,Triton,Yuanti}, -r {Aasimar,Bugbear,Dragonborn,Dwarf,Elf,Firbolg,Gith,Gnome,Goblin,Goliath,HalfElf,HalfOrc,Halfling,Hobgoblin,Human,Kenku,Kobold,Lizardfolk,Orc,Tabaxi,Tiefling,Triton,Yuanti}
                        Sets your character's race    
                        (default: Human)
  -subrace SUBRACE, -sr SUBRACE
                        Sets your character's
                        subrace (default: )
  -sex {Female,Male}, -s {Female,Male}
                        Sets your character's sex     
                        (default: Female)
  -background {Acolyte,Charlatan,Criminal,Entertainer,Folk Hero,Guild Artisan,Hermit,Noble,Outlander,Sage,Sailor,Soldier,Urchin}, -b {Acolyte,Charlatan,Criminal,Entertainer,Folk Hero,Guild Artisan,Hermit,Noble,Outlander,Sage,Sailor,Soldier,Urchin}
                        Sets your character's
                        background (default:
                        Soldier)
  -klass {Barbarian,Bard,Cleric,Druid,Fighter,Monk,Paladin,Ranger,Rogue,Sorcerer,Warlock,Wizard}, -k {Barbarian,Bard,Cleric,Druid,Fighter,Monk,Paladin,Ranger,Rogue,Sorcerer,Warlock,Wizard}
                        Sets your character's class   
                        (default: Fighter)
  -subclass SUBCLASS, -sc SUBCLASS
                        Sets your character's
                        subclass (default: )
  -level {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20}, -l {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20}
                        Sets your character's level   
                        (default: 1)
  -threshold THRESHOLD, -t THRESHOLD
                        Sets the minimum ability      
                        score threshold (default:     
                        65)
  -port PORT, -p PORT   Sets server's port (default:  
                        5000)
  --roll-hp             Roll hit points every level after the first (default: False)
```


#### DISCLAIMER

This software is not affiliated with, endorsed, sponsored, or specifically approved
by Wizards of the Coast LLC. This software is a fan made tool.
