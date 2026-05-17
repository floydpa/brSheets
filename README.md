This project is a Python backend web service for interacting with a Google Sheet to record horse racing bets.

The representation of the schema for the Google Sheet transactions is defined in SheetSpec.json.

In the first version of this application the REST API will provide the following functions:
1) Insert a new draft bet. This is a tip that has not yet been placed with a bookmaker. See file draftBet.md
2) Update an existing draft bet to create an open bet. This updates the transaction after the bet has been placed with a bookmaker. See openBet.md
3) Update an existing open bet. Update an existing transaction row once the race has been run and the bet has been settled.
4) Provide a list of transactions for the sheet. Filters can be provided as part of this request to limit what is returned.

Batch imports of draft bets
---------------------------
Place multiple JSON files representing draft bets in the draft_bets directory.
Start the FastAPI service if not already running (fastapi dev main.py)
Check FastAPI service is running (http://127.0.0.1:8000/docs)
From the terminal run:
    python import_drafts.py

Racing Post data
----------------
Note that the 'rpscrape' subdirectrory has been created from the 'rpscrape' project on github
    git clone https://github.com/joenano/rpscrape.git
This is used to collect race results including the SP.
It's possible to extract a huge amount of data, but I've simplified it to just position, horse and SP.

