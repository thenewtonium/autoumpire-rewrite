# autoumpire-rewrite
 A rewritten version of the AutoUmpire software used by the Cambridge Assassin's Guild.
 
## Introduction

This software is intended to replace the AutoUmpire 0.3 software written by Matthew Johnson & co. in 2004(?). The current software is difficult to use, according to recent Umpires, and could do with being updated to be more friendly to people who do not spend all their time programming.

AutoUmpire 0.3 is written in Java. The README claims it is designed to be easily extensible. However, it is poorly documented, and hence puzzling through the thousands[^1] of lines of code -- much of it boilerplate (as is usual for Java) and scattered across many many class files -- is not worth it.

[^1]: I have not actually counted, but it is a lot.

My rewrite will use Python 3. This is not because I think it is the best language for this kind of software, but because this is a standard language that most STEM students nowadays have some familiarity with, which should help future maintenance of the program.

Ideally my rewrite should be easy enough for a non-technical user that this is not really *necessary*, but I wish to avoid the same situation we have now recurring in another 20 year's time.

## Features of the program
First I will write a command-line version, implementing similar commands to the current AutoUmpire (however I will not require the interface to be identical, as this is precisely the thing I am trying to improve!)

~~Data storage will use MongoDB. This is because it stores data on disk in JSON format, which is human-readable.~~ *I will in fact use SQLAlchemy, and Python classes. I hope to however write it in an easier-to-comprehend way than the source code of the current version -- at the very least it will have more comments!

The tasks the program needs to be able to achieve are

- [ ] Load in player data.
	- This will be done in CSV format for bulk-loading -- whatever spreadsheet program is popular in $currentyear will likely support CSV editing, and I will provide an example formatting of how the file should look for the program to parse it.
	- Individual commands to add/edit/remove players will also be provided.
	- Like the original program (from a cursory glance), Players and Assassins will be seperate databases. Databases referring to players will 
		- `Players` includes information such as `Email`, `Real Name`, `Signup Type`, `Initial Pseudonym`, `Seed`, `Address`, `College`, `Water Weapons Status`, `Notes`. The first five are integral to the program. The rest are supplementary information that should be configurable in case the needs to the game change, such as happened during COVID.
		- `Assassins` will have fields `Pseudonyms`, `Targets`, `Assassins`, `Competence`, `Kills`, `Alive?`, `Killer`, `Died at`.
		- `Police` will have the fields `Pseudonyms`, `Rank`, `Alive?`, `Last Death`. Data which overlaps with `Assassins` is here rather than in `Players` in order to keep activities as a Full Player seperate from activities as Police. (In Mayweek all players will be Police).
- [ ] Start the game
	- This will initialise the `Assassins` database from `Players`. This includes generating targets
	- My understanding of the current targetting algorithm is that it initialises as follows:
		1. First it allocates targets at random until everyone has 3 targets and 3 assassins, avoiding symmetric and reflexive targetting.
		2. Next it checks for any 3-cycles in the targetting graph and creates a list of the assassins involved.
		3. If there are any 3-cycles, it randomly attempts to remove on average a fifth of the assassins/targets of each player, and then a half of the assassins/targets of each player that were in 3-cycles. It then "refills" the targets/assassins of each player, and goes back to 2.
		4. Otherwise, the targetting is valid, and then it does some clever seeding algorithm to place highly-seeded assassins as 'far' from each other as possible.
		
		As far as retargetting after deaths is concerned, I have not determined how the algorithm does this.
- [ ] Register an attempt
	- Each player will have an attempts counter.
	- When this hits a specified value (2) comptetence is granted.
- [ ] Register a kill
	- The dead player will be set to dead. All the dead player's targets will have the dead player removed as an assassin. All the dead player's assasins will have the dead player removed as a target. 
	- The killer will be granted competence.
	- The retargetting algorithm will run.
	- Something should probably happen with a kill tree.
	- Attempts counter being reset or not is something that can be configured.
- [ ] Add an event
	- An event consists of a `Timestamp`, `Headline`, `Involved Players` and several `Reports`,
	- Each report has an `Author` and `Body`.
	- We need to have a way of substituting pseudonyms. The current system replaces real names in [] with pseudonyms. There is a problem here if anyone ever has the same real name, hence I suggest instead giving the email like `<acn44@cam.ac.uk>` instead and having this replaced by psydonym.
	- The `Involved Players` data specifies how each player should be displayed, i.e. pseudonym and colour, and whether they are dead. Being dead only affects display in the headline.
	- Alternatively I could use some syntax like `!<acn44@cam.ac.uk>` to have an email replaced with the dead-player format.
- [ ] Add a report to an existing event
- [ ] Edit the data in reports/events
- [ ] Delete reports/events, in case of a mistake
- [ ] Generate News and Reports pages from game data.
	- The current autoumpire uses a smart xml-based generation system.
- [ ] Email players on various events
	- New targets
	- Announcements
	- Competency deadline approaching
- [ ] Enter Open Season
- [ ] Create an Incomptent list
	- There is no extra data to store here; this could be generated directly from the `Assassins` database.
- [ ] Create a Wanted/Corrupt list
	- Data needed are `Crime` and `Redemption conditions`.
	- Also the 'list of corpses'.
	- Command to send someone wanted.
	- Command to redeem them.
- [ ] Thunderbolt a player

## Files
- `config.json`: contains the configuration data for AutoUmpire. Config options are
    - `db_address`: address for the database for SQLAlchemy to use. For sqlite, which stores the database as an on-disk file, the format is `sqlite+pysqlite:///[filename]`
- `assassins_data.py` a module file setting up the connection to the database, and defining Classes representing the data stored therein such as `Player`, `Assassin`, `Police`, `Event`, `Report`, `TargetGroup`, ...

## "Polishing-up" to-do
These are ways in which I want to refactor the code to improve error handling etc
- [ ] Make Email Class to simplify validation. Would like to auto-cast crsIDs to emails, but may be problematic?
- [ ] Make Colleges enum (in its own file for easy adding)
- [ ] More file separation? idk