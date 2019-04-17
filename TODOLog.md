# 17/04/19
Added a bunch of the older shows to my shows.yaml. 
A thought: a way to combine shows into tapings (optionally) might be nice.

Next:
- Pretty up the webpage
- Fill out my shows.yaml so we've got a more representative data set
- How do we handle multiple promotion shows? I should test that.

Still To Do:
- Figure out how to deal with duplicates. Currently any duplicate workers, shows, or promotions are skipped. For workers, we really want to check if their ID exists, and if it does, append the gimmick name to the "name" field if it's not already in there. This could be a "nice to have" though.
- It occured to me that we don't deal in any way with the matches on a show, so we
    - have no distinction for managers rather than matches
    - have no way to deal with people having multiple matches on a shows
  Could we address this with a 'times' column in the appearances table maybe?
- A way to merge shows into a single taping might be nice (for example candidates, see April 2010 in shows.yaml)
- Figure out how to deal with multiple runs. In an ideal world, we shouldn't have to drop the database between runs, we should figure out which shows are loaded already and not re-add them. We also try to create the tables each run.
- maybe extract the schema and queries to a .sql file?
- clean it up a little
- document some of the weirder bits of BS magic for my own sake. probably just in here.

# 16/04/19
Got a couple of tables now!
Added two queries to count up the number of appearances for each worker, and the number of shows for each promotion.
Added pandas to read the SQL (using read_sql_query) into a DataFrame
The DataFrames are then fed into two simple pie charts to display the data!

Next:
- Pretty up the webpage
- Fill out my shows.yaml so we've got a more representative data set
- How do we handle multiple promotion shows? I should test that.

Still To Do:
- Figure out how to deal with duplicates. Currently any duplicate workers, shows, or promotions are skipped. For workers, we really want to check if their ID exists, and if it does, append the gimmick name to the "name" field if it's not already in there. This could be a "nice to have" though.
- It occured to me that we don't deal in any way with the matches on a show, so we
    - have no distinction for managers rather than matches
    - have no way to deal with people having multiple matches on a shows
  Could we address this with a 'times' column in the appearances table maybe?
- Figure out how to deal with multiple runs. In an ideal world, we shouldn't have to drop the database between runs, we should figure out which shows are loaded already and not re-add them. We also try to create the tables each run.
- maybe extract the schema and queries to a .sql file?
- clean it up a little
- document some of the weirder bits of BS magic for my own sake. probably just in here.

# 27/03/19
All the details that I was extracting previously now get put into a database 👍

Next:
- Figure out how to deal with duplicates. Currently any duplicate workers, shows, or promotions are skipped. For workers, we really want to check if their ID exists, and if it does, append the gimmick name to the "name" field if it's not already in there. This could be a "nice to have" though.
- Figure out how to deal with multiple runs. In an ideal world, we shouldn't have to drop the database between runs, we should figure out which shows are loaded already and not re-add them. We also try to create the tables each run.
- Start doing some web stuff/graphing! Well, at least figure out the SQL for getting the data for those.

Still To Do:
- maybe extract the schema to a .sql file?
- clean it up a little
- document some of the weirder bits of BS magic for my own sake. probably just in here.

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
