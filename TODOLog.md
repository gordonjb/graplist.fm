# 22/04/19
Added request caching, using [requests-cache](https://pypi.org/project/requests-cache/). It caches to a SQLite database `cagematch_cache.sqlite`, currently I never expire the cache. We can probably add something later to invalidate cache objects when we need to. For my current purposes, I can just delete it.

Also adds argparse, and two arguments:
`-f`/`--file` specifies the yaml file of shows to load, meaning I can use the test show list instead. This was useful as a small set to test the cache, and similarly for edge cases later.
`-v`/--verbose` will also output the full worker string from the comma separated list.

I added the Cagematch URL to the shows table, no immediate need for it, but it'll be useful later I imagine.

In further non essential changes, I changed the database types to actually match what SQLite uses. [Reference](https://www.sqlite.org/datatype3.html).

I just realised I never documented the commands I'm using to run.

Currently:
- to reload/initialise the database: `rm -f thedatabase.sqlite3 && pipenv run python graps.py`
- to start the webserver and serve the stats: `pipenv run python app.py`

# 17/04/19
Added a bunch of the older shows to my shows.yaml.

Extracted the actual todo list to a [Kanban board](https://github.com/gordonjb/graplist.fm/projects/3)

A thought: a way to combine shows into tapings (optionally) might be nice.

# 16/04/19
Got a couple of tables now!

Added two queries to count up the number of appearances for each worker, and the number of shows for each promotion.

Added pandas to read the SQL (using read_sql_query) into a DataFrame

The DataFrames are then fed into two simple pie charts to display the data!

# 27/03/19
All the details that I was extracting previously now get put into a database 👍

# 26/03/19
Added method to create table schema

# 17/03/19
Enough is working that I feel happy committing it
- Reads shows from YAML file
- Parses out show info
- Parses All Workers list to get ID and Name pairs

Next:
- put that info into something useful, probably an SQLite database
- figure out useful schema for that db
- clean it up a little
- document some of the weirder bits of BS magic for my own sake. probably just in here.
