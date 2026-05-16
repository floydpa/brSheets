# Data for recreation of a Google Sheet that should match the one maintained manually

scripts
=======


data directory
==============

placed_bets
-----------
This is the list of tips that should be used to create a set of draft bets to match what has been placed.

missed_bets
-----------
This is a list of tips that weren't placed as actual bets for one reason or another.
These will be found in the tip messages, but not in the manually maintained Google Sheet.

non_runners
-----------
This is a list of tips that can be found in the tip messages but turned out to be non-runners so are not in the Google Sheet

other_bets
----------
This is a list of bets that have come from other sources so cannot be found in the Telegram tip messages.
This set of files has also been included in placed_bets.

historical_openings.csv
-----------------------
This file holds data to indicate how draft bets were placed.
Use the script split_openings.py to create one JSON file per line in bet_placings
Then use the script import_placings.py to update the Google Sheet that contains draft bets

bet_placings
------------
Contains a set of JSON files that are created from import_placings.py

