@app.get("/coaches")
def get_coaches():
    return {
        "coaches": [
          
            {"id": 181, "name": "Mumble Brown", "team": "Biripi Dolphins"},
            {"id": 182, "name": "Bryan McVey", "team": "St Marys Notorious"},
            {"id": 183, "name": "Peter Barlow", "team": "Kanima Kookaburras"},
            {"id": 184, "name": "Brody Walker", "team": "Bidwill Body Baggers"},
            {"id": 185, "name": "Jacob Mathews-Laws", "team": "Vegemite Village Villans"},
          
            {"id": 191, "name": "William Forster", "team": "Dharug Dinos"},
            {"id": 192, "name": "Taylor Russell", "team": "Narellan Kangaroos"},
            {"id": 193, "name": "Tyson Manhire", "team": "Jaldamany Brothers"},
            {"id": 194, "name": "Brayden Alpine", "team": "Alpine Mountaineers"},
            {"id": 195, "name": "Stephen Merideth", "team": "Merideth Tigers"},
            {"id": 196, "name": "Michael", "team": "East Coast Pirates"},
            {"id": 197, "name": "Connor Sanki", "team": "Baludarri Runners"},
            {"id": 198, "name": "Nathan Waterman", "team": "Nathan Patrollers"},
            {"id": 199, "name": "Hayden Farringdon", "team": "Parramatta 60's"},
            {"id": 1910, "name": "James Cryer", "team": "Ngapuhi Warriors"},
            {"id": 1911, "name": "Lachlan Pittman", "team": "Yuin Blackducks"},
            {"id": 1912, "name": "Jake Davies", "team": "Port Macquarie Puddle-Ducks"},
            {"id": 1913, "name": "Brodie Russell", "team": "Russell Vale Cobras"},

            {"id": 201, "name": "Dale Benwall", "team": "Bellbrook Boobcats"},
          
            {"id": 211, "name": "Holly Waterman", "team": "Holsworthy Watermans"},
          
            {"id": 221, "name": "Jack Landow", "team": "Melbourne Magicians"},
            {"id": 222, "name": "Jack Maladay", "team": "Northern Lightning"},
            {"id": 223, "name": "Tyson Johnston", "team": "Tyson 95ers"},

            {"id": 231, "name": "Justin Elks", "team": "Elkwood Reindeers"},
            {"id": 232, "name": "Luke Forster", "team": "Forster Barbarians"},

            {"id": 251, "name": "Josh Harvey", "team": "Harvey Bay Nautiluses"},
            {"id": 252, "name": "Andrew Jackson-Smith", "team": "Wiradjuri Goannas"},

            {"id": 261, "name": "Shafilly Hussein", "team": "Hermitage Chefs"},
            {"id": 262, "name": "Gabriel Drummond", "team": "Drummond Roosters"},
            {"id": 263, "name": "Jakob Cryer", "team": "Mount Austin Panthers"},
            {"id": 264, "name": "Sage King", "team": "Wagga-Wagga Rams"}
        ]
    }

@app.get("/admin")
def get_admin():
    return {
        "admin": {
            "id": 1,
            "name": "Benjamin McKeever",
            "role": "Commissioner",
            "permissions": "all"
        }
    }
