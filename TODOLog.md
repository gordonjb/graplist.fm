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
