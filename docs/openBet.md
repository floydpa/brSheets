This is a sample JSON payload representing a new open bet based on a previous tip with the same ID.

{
  "ID": "trn234",
  "bookmaker": "bet365",
  "oddsTaken": "6/1",
  "bog": "Yes",
  "placesPaid": "4",
  "placeFraction": "1/5",
  "gbpPerPoint": 10.0
}

When this is used to update an existing row with the same ID in the Google Sheet transactions, the 'Status' field should be changed to 'Open'.

All other fields (including those defined with formulae) should retain the values used when created from the draft bet.

Notes:
======

The field 'Pt (£)' will be set from 'gbpPerPoint'. This is a user-defined value which would be held as part of that user's profile in the agent sending the open bet to us.

The Bookmaker field can now be set from '-' to one of the other items in the picklist:
    bet365
    Ladbrokes
    William Hill
    BetVictor
    Betfred
    skybet

Each has a background colour set similar to that used on their company logo to more easily identify them, e.g. green for bet365 and red for Ladbrokes.

The BOG field can now be set from '-' to either 'Yes' or 'No' depending on what the bookmaker offered for that bet.

The PlcFraction field can now be set from '-' to one of the other items in the picklist based on what the bookmaker offered on an each way bet:
    1/5
    1/4

