import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: Supabase credentials not found in .env")
    exit()

supabase = create_client(url, key)

# --- Data from script.js ---

teams_s1 = [
    { "name": "Avin puliken", "season": "season1", "played": 10, "won": 4, "drawn": 1, "lost": 5, "gf": 25, "ga": 31, "points": 13, "form": "LLLWWDLLLW" },
    { "name": "Basil sabu", "season": "season1", "played": 10, "won": 2, "drawn": 1, "lost": 7, "gf": 19, "ga": 36, "points": 7, "form": "LLLWLDWWLD" },
    { "name": "Chris john George", "season": "season1", "played": 10, "won": 6, "drawn": 0, "lost": 4, "gf": 32, "ga": 18, "points": 18, "form": "WLWLWWWWLL" },
    { "name": "Christo shaju", "season": "season1", "played": 10, "won": 7, "drawn": 0, "lost": 3, "gf": 24, "ga": 15, "points": 21, "form": "LWLWWWWLW" },
    { "name": "Basil santhosh", "season": "season1", "played": 10, "won": 5, "drawn": 1, "lost": 4, "gf": 18, "ga": 14, "points": 16, "form": "WWWLDLLWWL" },
    { "name": "Basil Eldo", "season": "season1", "played": 10, "won": 4, "drawn": 1, "lost": 5, "gf": 19, "ga": 26, "points": 13, "form": "LLLLWWLDWW" }
]

# Raw fixtures from script.js converted to dicts
fixtures_s1 = [
    ["Basil sabu", "Avin puliken", 1, 2, 7],
    ["Chris john George", "Christo shaju", 1, 3, 1],
    ["Basil santhosh", "Basil Eldo", 1, 5, 1],
    ["Christo shaju", "Basil sabu", 2, 2, 0],
    ["Basil Eldo", "Avin puliken", 2, 2, 3],
    ["Basil santhosh", "Chris john George", 2, 0, 1],
    ["Basil sabu", "Basil Eldo", 3, 1, 2],
    ["Christo shaju", "Basil santhosh", 3, 6, 3],
    ["Avin puliken", "Chris john George", 3, 1, 6],
    ["Basil santhosh", "Basil sabu", 4, 5, 2],
    ["Chris john George", "Basil Eldo", 4, 1, 7],
    ["Avin puliken", "Christo shaju", 4, 1, 3],
    ["Basil sabu", "Chris john George", 5, 2, 8],
    ["Basil santhosh", "Avin puliken", 5, 0, 1],
    ["Basil Eldo", "Christo shaju", 5, 2, 1],
    ["Avin puliken", "Basil sabu", 6, 4, 4],
    ["Christo shaju", "Chris john George", 6, 2, 0],
    ["Basil Eldo", "Basil santhosh", 6, 0, 0],
    ["Basil sabu", "Christo shaju", 7, 1, 2],
    ["Avin puliken", "Basil Eldo", 7, 1, 5],
    ["Chris john George", "Basil santhosh", 7, 0, 1],
    ["Basil Eldo", "Basil sabu", 8, 3, 4],
    ["Basil santhosh", "Christo shaju", 8, 0, 1],
    ["Chris john George", "Avin puliken", 8, 2, 4],
    ["Basil sabu", "Basil santhosh", 9, 2, 1],
    ["Basil Eldo", "Chris john George", 9, 2, 3],
    ["Christo shaju", "Avin puliken", 9, 5, 0],
    ["Chris john George", "Basil sabu", 10, 2, 1],
    ["Avin puliken", "Basil santhosh", 10, 1, 2],
    ["Christo shaju", "Basil Eldo", 10, 1, 4]
]

fixtures_knockout = [
    ["Christo shaju", "Basil santhosh", 'SF1', 4, 2],
    ["Avin puliken", "Chris john George", 'SF2', 2, 3],
    ["Christo shaju", "chris john George", 'Final', 3, 1]
]

def seed():
    print("Seeding Teams...")
    try:
        data = supabase.table("teams").select("*").execute()
        if len(data.data) == 0:
            supabase.table("teams").insert(teams_s1).execute()
            print("Teams seeded.")
        else:
            print("Teams table already has data.")
    except Exception as e:
        print(f"Error seeding teams: {e}")

    print("Seeding Fixtures...")
    try:
        data = supabase.table("fixtures").select("*").execute()
        if len(data.data) == 0:
            # Process fixtures
            formatted_fixtures = []
            for f in fixtures_s1:
                formatted_fixtures.append({
                    "home_team": f[0], "away_team": f[1], 
                    "round": str(f[2]), 
                    "home_score": f[3], "away_score": f[4],
                    "season": "season1", "status": "Completed",
                    "date": "2024-10-28", "time": "FT", "venue": "Basil Arena"
                })
            for f in fixtures_knockout:
                formatted_fixtures.append({
                    "home_team": f[0], "away_team": f[1], 
                    "round": str(f[2]), 
                    "home_score": f[3], "away_score": f[4],
                    "season": "season1", "status": "Completed",
                    "date": "2024-12-20", "time": "FT", "venue": "Basil Arena"
                })
            
            supabase.table("fixtures").insert(formatted_fixtures).execute()
            print("Fixtures seeded.")
        else:
            print("Fixtures table already has data.")
    except Exception as e:
        print(f"Error seeding fixtures: {e}")

if __name__ == "__main__":
    seed()
