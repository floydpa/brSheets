This is a sample JSON payload representing a draft bet

{
  "ID": "trn234",
  "raceDate": "06/05/2026",
  "racecourse": "Chester",
  "raceTime": "14:05",
  "horse": "Supido",
  "tipster": "TOF",
  "stakePts": 0.50,
  "betType": "E/W",
  "advisedOdds": "l6/1",
  "advisedPlaces": "4"
}

These values must be used to add a new transaction record to the Sheet. The 'Status' field on that record should be set to 'Draft'.

Other fields must be set to default values as follows:

{
  "bookmaker": "-",
  "oddsTaken": "",
  "bog": "-",
  "placesPaid": "",
  "placeFraction": "-",
  "gbpPerPoint": 0.0,
  "position": "",
  "sp": "",
  "rule4": ""
}

All formula fields should be initialised with their predefined formulae to create a complete row.

Notes:
======

Date will always be in DD/MM/YYYY format.

Time will always be 24h HH:MM format.

Tipster will be a short code, e.g. TOF for 'Turn Of Foot'.

The AdvPlc field may be blank if there are no advised places as part of the tip.

Bet Type can be either 'E/W' or 'Win'.

The Bookmaker field is a picklist with the following options defined (where '-' is used to mean not yet set):
    -
    bet365
    Ladbrokes
    William Hill
    BetVictor
    Betfred
    skybet

Each has a background colour set similar to that used on their company logo to more easily identify them, e.g. green for bet365 and red for Ladbrokes.

The BOG field is a picklist with the following options defined (where '-' is used to mean not yet set):
    -
    Yes
    No

The PlcFraction is a picklist with the following options defined (where '-' is used to mean not yet set):
    -
    1/5
    1/4

Other options may be possible for the place fraction, but I've not seen them yet. FreeBetCalculator has 1/1, 1/2, 1/3, 1/4, 1/5 and 1/6.

The field 'Pt (£)' will be set later once the bet has been placed. A tip will always be given in terms of points so the user will convert to real money using a factor that fits his budget, e.g. 1 pt equals £10.

