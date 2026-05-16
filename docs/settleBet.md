This is a sample JSON payload representing the settlement of an existing open bet.

{
    "ID": "trn234",
    "status": "Won",
    "position": "1",
    "sp": "15/2",
    "rule4": ""
}

When this is used to update an existing row with the same ID in the Google Sheet transactions, the 'Status' field should be changed to:
    Won    - if the horse won the race
    Placed - if the bookmaker paid out on a place
    Lost   - if the bet lost
    Void   - if the stake was returned, e.g. non-runner

All other fields (including those defined with formulae) should retain the values used when created from the draft bet.

