# autoumpire-rewrite
 A rewritten version of the AutoUmpire software used by the Cambridge Assassin's Guild.
 
## About AutoUmpire

This software is intended to replace the AutoUmpire 0.3 software written by Matthew Johnson & co. in 2004(?). The current software is difficult to use, according to recent Umpires, and could do with being updated to be more friendly to people who do not spend all their time programming.

AutoUmpire 0.3 is written in Java. The README claims it is designed to be easily extensible. However, it is poorly documented, and hence puzzling through the thousands[^1] of lines of code -- much of it boilerplate (as is usual for Java) and scattered across many many class files -- is not worth it.

[^1]: I have not actually counted, but it is a lot.

My rewrite will use Python 3. This is not because I think it is the best language for this kind of software, but because this is a standard language that most STEM students nowadays have some familiarity with, which should help future maintenance of the program.

Ideally my rewrite should be easy enough for a non-technical user that this is not really *necessary*, but I wish to avoid the same situation we have now recurring in another 20 year's time.

## This project

This version of AutoUmpire is split into two parts:

`au_core`
: a module implementing the fundamental logic of the game.
It uses SQLAlchemy to define classes whose instances essentially represent rows of various tables in the games database.
The structure is based around a `Game` class,
which stores game settings and implements 'top-level' game functions,
such as assigning targets and generating headlines/news pages.

`au_cli`
: implements a command line interface (hence 'cli') for AutoUmpire.
All the files (apart from `__main__.py`, which is the main program,
and `commands.py` which defines the interface by which other files can add commands)
double as a stand-alone script that can be run directly from bash or other terminal of choice --
though use of the main cli is recommended over this.

A third part, which I provisionally refer to as `au_web`,
is intended to provide a web-based interface for interaction with AutoUmpire.
This would most likely use Flask as the basis.
I will only start work on this once I am satisfied with `au_core`.
`au_cli` had to be developed in tandem with `au_core` for testing purposes
(which is why the direct-from-terminal operation exists)
but the less code dependent on the in-progress bodge of `au_core`, the better.