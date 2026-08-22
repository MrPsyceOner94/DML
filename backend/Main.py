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

@app.get("/draft-order")
def get_draft_order():
    return {
        "draft": {
            "season": 2026,
            "format": "Snake",
            "status": "Scheduled",
            "round_1": [
                {"pick": 1, "coach_id": 182, "name": "Bryan McVey", "team": "St Marys Notorious"},
                {"pick": 2, "coach_id": 197, "name": "Connor Sanki", "team": "Baludarri Runners"},
                {"pick": 3, "coach_id": 191, "name": "William Forster", "team": "Dharug Dinos"},
                {"pick": 4, "coach_id": 264, "name": "Sage King", "team": "Wagga-Wagga Rams"},
                {"pick": 5, "coach_id": 262, "name": "Gabriel Drummond", "team": "Drummond Roosters"},
                {"pick": 6, "coach_id": 199, "name": "Hayden Farringdon", "team": "Parramatta 60's"},
                {"pick": 7, "coach_id": 222, "name": "Jack Maladay", "team": "Northern Lightning"},
                {"pick": 8, "coach_id": 221, "name": "Jack Landow", "team": "Melbourne Magicians"},
                {"pick": 9, "coach_id": 263, "name": "Jakob Cryer", "team": "Mount Austin Panthers"},
                {"pick": 10, "coach_id": 1910, "name": "James Cryer", "team": "Ngapuhi Warriors"},
                {"pick": 11, "coach_id": 181, "name": "Mumble Brown", "team": "Biripi Dolphins"},
                {"pick": 12, "coach_id": 261, "name": "Shafilly Hussein", "team": "Hermitage Chefs"},
                {"pick": 13, "coach_id": 192, "name": "Taylor Russell", "team": "Narellan Kangaroos"},
                {"pick": 14, "coach_id": 193, "name": "Tyson Manhire", "team": "Jaldamany Brothers"}
            ]
        }
    }

@app.get("/rosters")
def get_rosters():
    return {
        "round": 1,
        "rosters": [
            {
                "team": "St Marys Notorious",
                "coach_id": 182,
                "lineup": {
                    "hooker": [{"id": 100001349, "name": "Chris Randall"}],
                    "front_row": [
                        {"id": 507915, "name": "Trey Mooney"},
                        {"id": 501267, "name": "Mitchell Barnett"},
                        {"id": 100006241, "name": "Hamish Stewart"}
                    ],
                    "second_row": [
                        {"id": 507062, "name": "Briton Nikora"},
                        {"id": 509529, "name": "Tallis Duncan"}
                    ],
                    "halves": [
                        {"id": 502490, "name": "Nicholas Hynes", "role": "Captain"},
                        {"id": 100003925, "name": "Ethan Sanders"}
                    ],
                    "centres": [
                        {"id": 506682, "name": "Bradman Best"},
                        {"id": 504294, "name": "Campbell Graham"}
                    ],
                    "wing_fullbacks": [
                        {"id": 504870, "name": "Kalyn Ponga", "role": "Vice Captain"},
                        {"id": 501505, "name": "Tom Trbojevic"},
                        {"id": 100009209, "name": "Keano Kini"}
                    ]
                },
                "bench": [
                    {"id": 505811, "name": "Adam Doueihi"},
                    {"id": 503419, "name": "Brandon Smith"},
                    {"id": 501559, "name": "Charnze Nicoll-Klokstad"},
                    {"id": 507922, "name": "Will Penisini"}
                ]
            },
            {
                "team": "Baludarri Runners",
                "coach_id": 197,
                "lineup": {
                    "hooker": [{"id": 504274, "name": "Blayke Brailey"}],
                    "front_row": [
                        {"id": 500555, "name": "Joseph Tapine"},
                        {"id": 500973, "name": "Josh Papalii"},
                        {"id": 500622, "name": "Tyson Frizell"}
                    ],
                    "second_row": [
                        {"id": 505582, "name": "Dylan Lucas"},
                        {"id": 510577, "name": "Samuela Fainu"}
                    ],
                    "halves": [
                        {"id": 504363, "name": "Kyle Flanagan"},
                        {"id": 504121, "name": "Jarome Luai"}
                    ],
                    "centres": [
                        {"id": 500845, "name": "Valentine Holmes"},
                        {"id": 508009, "name": "Kotoni Staggs"}
                    ],
                    "wing_fullbacks": [
                        {"id": 505410, "name": "Brian To'o"},
                        {"id": 100001634, "name": "Xavier Coates"},
                        {"id": 501351, "name": "Josh Addo-Carr"}
                    ]
                },
                "bench": [
                    {"id": 100003898, "name": "Ryley Smith"},
                    {"id": 100010997, "name": "Will Warbrick"},
                    {"id": 500265, "name": "Kodi Nikorima"},
                    {"id": 100011655, "name": "Jacob Halangahu"}
                ]
            },
            {
                "team": "Dharug Dinos",
                "coach_id": 191,
                "lineup": {
                    "hooker": [{"id": 508629, "name": "Jake Simpkin"}],
                    "front_row": [
                        {"id": 505976, "name": "Isaiah Papali'i"},
                        {"id": 505628, "name": "Stefano Utoikamanu"},
                        {"id": 502580, "name": "James Fisher-Harris"}
                    ],
                    "second_row": [
                        {"id": 500459, "name": "Luciano Leilua"},
                        {"id": 100013674, "name": "Leka Halasima"}
                    ],
                    "halves": [
                        {"id": 100007336, "name": "Lachlan Galvin", "role": "Vice Captain"},
                        {"id": 100006524, "name": "Ethan Strange"}
                    ],
                    "centres": [
                        {"id": 500339, "name": "Jack Wighton"},
                        {"id": 509467, "name": "Izack Tago"}
                    ],
                    "wing_fullbacks": [
                        {"id": 510216, "name": "Reece Walsh", "role": "Captain"},
                        {"id": 507846, "name": "Kaeo Weekes"},
                        {"id": 503443, "name": "Reuben Garrick"}
                    ]
                },
                "bench": [
                    {"id": 510696, "name": "Setu Tu"},
                    {"id": 500109, "name": "Apisai Koroisau"},
                    {"id": 506153, "name": "Ethan Bullemor"},
                    {"id": 100007572, "name": "Leo Thompson"}
                ]
            }
        ]
    }

