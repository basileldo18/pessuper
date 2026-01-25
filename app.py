from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from datetime import timedelta
from supabase import create_client, Client
import pandas as pd
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)

# Supabase Setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Warning: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    supabase = None
else:
    supabase: Client = create_client(url, key)

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not supabase:
            flash("Database not connected", "error")
            return redirect(url_for('landing'))

        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            session.permanent = True
            session['user'] = response.user.email
            session['access_token'] = response.session.access_token
            return redirect(url_for('admin'))
        except Exception as e:
            flash(str(e), "error")
            return redirect(url_for('landing'))
            
    return render_template('landing.html', login_mode=True)

@app.route('/points')
def points():
    # Fetch data from Supabase to pass to the frontend
    if not supabase:
        # Fallback empty structure if DB not connected
        league_data = {"season1": {"teams": [], "fixtures": []}, "season2": {"teams": [], "fixtures": []}}
    else:
        try:
            # Fetch teams
            teams_response = supabase.table('teams').select("*").execute()
            teams = teams_response.data
            
            # Fetch fixtures
            fixtures_response = supabase.table('fixtures').select("*").execute()
            fixtures = fixtures_response.data
            
            # Organize by season
            league_data = {
                "season1": {
                    "teams": [t for t in teams if t['season'] == 'season1'],
                    "fixtures": [f for f in fixtures if f['season'] == 'season1']
                },
                "season2": {
                    "teams": [t for t in teams if t['season'] == 'season2'],
                    "fixtures": [f for f in fixtures if f['season'] == 'season2']
                },
                "season3": {
                    "teams": [t for t in teams if t['season'] == 'season3'],
                    "fixtures": [f for f in fixtures if f['season'] == 'season3']
                }
            }
        except Exception as e:
            print(f"Error fetching data: {e}")
            league_data = {"season1": {"teams": [], "fixtures": []}, "season2": {"teams": [], "fixtures": []}, "season3": {"teams": [], "fixtures": []}}

    return render_template('index.html', league_data=json.dumps(league_data))

# Helper to re-calculate league table from fixtures
def calculate_standings(season):
    if not supabase or not season: return

    # 1. Fetch all completed fixtures and all teams
    # Order by ID to ensure roughly chronological processing for form
    fixtures = supabase.table('fixtures').select('*').eq('season', season).eq('status', 'Completed').order('id').execute().data
    teams_data = supabase.table('teams').select('id, name').eq('season', season).execute().data
    
    # Initialize stats for all teams to 0
    stats = {
        t['name']: {
            'id': t['id'], 
            'name': t['name'], 
            'season': season,
            'played': 0, 'won': 0, 'drawn': 0, 'lost': 0, 
            'gf': 0, 'ga': 0, 'points': 0,
            'form_list': [] # Temporary list for calculation
        } 
        for t in teams_data
    }
    
    # 2. Aggregate stats from fixtures
    for f in fixtures:
        # Exclude Knockout Stages from League Table
        if str(f['round']) in ['SF1', 'SF2', 'Final', 'QF1', 'QF2', 'QF3', 'QF4']:
            continue

        home = f['home_team']
        away = f['away_team']
        if f['home_score'] is None or f['away_score'] is None: continue
        
        h_score = int(f['home_score'])
        a_score = int(f['away_score'])
        
        # Only process if both teams exist in our team list
        if home in stats and away in stats:
            stats[home]['played'] += 1
            stats[away]['played'] += 1
            stats[home]['gf'] += h_score
            stats[away]['gf'] += a_score
            stats[home]['ga'] += a_score
            stats[away]['ga'] += h_score
            
            if h_score > a_score:
                stats[home]['won'] += 1
                stats[home]['points'] += 3
                stats[away]['lost'] += 1
                stats[home]['form_list'].append('W')
                stats[away]['form_list'].append('L')
            elif a_score > h_score:
                stats[away]['won'] += 1
                stats[away]['points'] += 3
                stats[home]['lost'] += 1
                stats[away]['form_list'].append('W')
                stats[home]['form_list'].append('L')
            else:
                stats[home]['drawn'] += 1
                stats[away]['drawn'] += 1
                stats[home]['points'] += 1
                stats[away]['points'] += 1
                stats[home]['form_list'].append('D')
                stats[away]['form_list'].append('D')

    # 3. Process Form and Batch Update
    updates = []
    for data in stats.values():
        # Get last 5 matches
        recent_form = data['form_list'][-5:]
        data['form'] = "".join(recent_form) # e.g. "WWLDL" (Concise) or ",".join for "W,W,L..."
        del data['form_list'] # Remove temp key
        updates.append(data)

    if updates:
        supabase.table('teams').upsert(updates).execute()


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session:
        return redirect(url_for('landing'))

    if request.method == 'POST':
        action = request.form.get('action')
        
        try:
            if action == 'update_team':
                # Bulk update for teams (Manual Override)
                team_ids = request.form.getlist('team_id')
                for t_id in team_ids:
                    data = {
                        'played': int(request.form.get(f'played_{t_id}') or 0),
                        'won': int(request.form.get(f'won_{t_id}') or 0),
                        'drawn': int(request.form.get(f'drawn_{t_id}') or 0),
                        'lost': int(request.form.get(f'lost_{t_id}') or 0),
                        'gf': int(request.form.get(f'gf_{t_id}') or 0),
                        'ga': int(request.form.get(f'ga_{t_id}') or 0),
                        'points': int(request.form.get(f'points_{t_id}') or 0),
                        'form': request.form.get(f'form_{t_id}', '').upper()
                    }
                    supabase.table('teams').update(data).eq('id', t_id).execute()
                
                flash("League table updated manually!", "success")
                
            elif action == 'update_fixture':
                match_id = request.form.get('match_id')
                home_score = request.form.get('home_score')
                away_score = request.form.get('away_score')
                
                update_data = {
                    'status': 'Completed'
                }
                
                if home_score and away_score:
                    update_data['home_score'] = int(home_score)
                    update_data['away_score'] = int(away_score)
                
                supabase.table('fixtures').update(update_data).eq('id', match_id).execute()
                
                # Auto-calculate Table
                fixture = supabase.table('fixtures').select('season').eq('id', match_id).single().execute().data
                if fixture:
                    calculate_standings(fixture['season'])

                flash("Match updated and table recalculated!", "success")

            elif action == 'add_team':
                team_name = request.form.get('team_name')
                season = request.form.get('season')
                if team_name and season:
                    supabase.table('teams').insert({
                        'name': team_name,
                        'season': season,
                        'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                        'gf': 0, 'ga': 0, 'points': 0, 'form': ''
                    }).execute()
                    flash(f"Team '{team_name}' added to {season}!", "success")
                else:
                    flash("Missing team name or season.", "error")

            elif action == 'import_season1':
                # Fetch Season 1 teams
                s1_teams = supabase.table('teams').select('*').eq('season', 'season1').execute().data
                
                # Insert them as Season 2 teams (reset stats)
                for team in s1_teams:
                    existing = supabase.table('teams').select('id').eq('season', 'season2').eq('name', team['name']).execute().data
                    if not existing:
                        supabase.table('teams').insert({
                            'name': team['name'],
                            'season': 'season2',
                            'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                            'gf': 0, 'ga': 0, 'points': 0, 'form': ''
                        }).execute()
                
                flash("Season 1 teams imported to Season 2 successfully!", "success")

            elif action == 'import_season2':
                # Fetch Season 2 teams
                s2_teams = supabase.table('teams').select('*').eq('season', 'season2').execute().data
                
                # Insert them as Season 3 teams (reset stats)
                for team in s2_teams:
                    existing = supabase.table('teams').select('id').eq('season', 'season3').eq('name', team['name']).execute().data
                    if not existing:
                        supabase.table('teams').insert({
                            'name': team['name'],
                            'season': 'season3',
                            'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                            'gf': 0, 'ga': 0, 'points': 0, 'form': ''
                        }).execute()
                
                flash("Season 2 teams imported to Season 3 successfully!", "success")

            elif action == 'delete_team':
                team_id = request.form.get('team_id')
                if team_id:
                    supabase.table('teams').delete().eq('id', team_id).execute()
                    flash("Team deleted successfully.", "success")

            elif action == 'delete_fixture':
                match_id = request.form.get('match_id')
                if match_id:
                    # Capture season before delete
                    fixture = supabase.table('fixtures').select('season').eq('id', match_id).single().execute().data
                    season_to_update = fixture['season'] if fixture else None
                    
                    supabase.table('fixtures').delete().eq('id', match_id).execute()
                    
                    # Recalculate table for that season
                    if season_to_update:
                        calculate_standings(season_to_update)
                        
                    flash("Fixture deleted and table recalculated.", "success")
            
            elif action == 'delete_all_fixtures':
                season = request.form.get('season')
                if season:
                    supabase.table('fixtures').delete().eq('season', season).execute()
                    calculate_standings(season) # Reset table
                    flash(f"All fixtures for {season} deleted successfully.", "success")
                    
            elif action == 'import_fixtures':
                season = request.form.get('season')
                file = request.files.get('fixtures_file')
                if file and file.filename.endswith(('.xlsx', '.xls')):
                    try:
                        df = pd.read_excel(file)
                        # Expected columns: Round, Home Team, Away Team
                        # Optional: Date, Time
                        
                        fixtures_to_insert = []
                        for index, row in df.iterrows():
                            home_team = row.get('Home Team')
                            away_team = row.get('Away Team')
                            round_name = row.get('Round')
                            
                            if home_team and away_team and round_name:
                                fixtures_to_insert.append({
                                    "season": season,
                                    "round": str(round_name),
                                    "home_team": home_team,
                                    "away_team": away_team,
                                    "home_score": None,
                                    "away_score": None,
                                    "status": "Scheduled"
                                })
                        
                        if fixtures_to_insert:
                            supabase.table('fixtures').insert(fixtures_to_insert).execute()
                            flash(f"{len(fixtures_to_insert)} fixtures imported successfully for {season}!", "success")
                        else:
                            flash("No valid fixtures found in file.", "warning")
                            
                    except Exception as e:
                        flash(f"Error importing fixtures: {str(e)}", "danger")
                else:
                    flash("Invalid file format. Please upload an Excel file.", "danger")

            elif action == 'generate_fixtures':
                season = request.form.get('season')
                match_type = request.form.get('match_type') # 'single' or 'double'
                
                # Fetch teams for season
                teams = supabase.table('teams').select('*').eq('season', season).execute().data
                
                if len(teams) < 2:
                    flash("Need at least 2 teams to generate fixtures.", "error")
                else:
                    is_double = (match_type == 'double')
                    # Generate fixtures
                    # Determine list of actual team dictionaries/objects
                    
                    # Round Robin Logic
                    rr_teams = list(teams)
                    if len(rr_teams) % 2 == 1:
                        rr_teams.append(None) # Bye
                    
                    n = len(rr_teams)
                    base_rounds = []
                    rotation = list(rr_teams)
                    
                    number_of_rounds_per_set = n - 1
                    
                    # Generate Base Schedule (Single Round Robin)
                    for r in range(number_of_rounds_per_set):
                        round_matches = []
                        for i in range(n // 2):
                            t1 = rotation[i]
                            t2 = rotation[n - 1 - i]
                            if t1 is not None and t2 is not None:
                                round_matches.append((t1, t2))
                        base_rounds.append(round_matches)
                        
                        # Rotate (Keep 0 fixed)
                        last = rotation.pop()
                        rotation.insert(1, last)
                    
                    new_fixtures = []
                    
                    try:
                        meetings_count = int(request.form.get('meetings_count', 1))
                    except ValueError:
                        meetings_count = 1

                    # Iterate for meetings count
                    for m in range(meetings_count):
                         # m=0: 1st meeting (Round 1..N-1)
                         # m=1: 2nd meeting (Round N..2N-2) -> Reverse Home/Away for variety
                         is_reverse = (m % 2 == 1) # Reverse on odd iterations (2nd, 4th...)

                         for r_idx, match_list in enumerate(base_rounds):
                            # Calculate sequential round number
                            current_round_num = (m * number_of_rounds_per_set) + r_idx + 1

                            for match in match_list:
                                home_t, away_t = match[0], match[1]
                                
                                home_name = home_t['name']
                                away_name = away_t['name']
                                
                                if is_reverse:
                                    home_name, away_name = away_name, home_name # Swap
                                
                                new_fixtures.append({
                                    "season": season,
                                    "round": str(current_round_num),
                                    "home_team": home_name,
                                    "away_team": away_name,
                                    "home_score": None, "away_score": None,
                                    "status": "Scheduled"
                                })
                    
                    if new_fixtures:
                        supabase.table('fixtures').insert(new_fixtures).execute()
                        flash(f"Generated {len(new_fixtures)} fixtures for {season}!", "success")
            
            elif action == 'approve_team_request':
                request_id = request.form.get('request_id')
                if request_id:
                    supabase.table('team_requests').update({'status': 'approved'}).eq('id', request_id).execute()
                    flash("Team request approved.", "success")
            
            elif action == 'decline_team_request':
                request_id = request.form.get('request_id')
                if request_id:
                    supabase.table('team_requests').update({'status': 'declined'}).eq('id', request_id).execute()
                    flash("Team request declined.", "success")
                
        except Exception as e:
            flash(f"Error updating: {e}", "error")
        
        return redirect(url_for('admin'))

    # GET request - Fetch data for admin view
    try:
        all_teams = supabase.table('teams').select('*').order('points', desc=True).execute().data
        all_fixtures = supabase.table('fixtures').select('*').order('id', desc=False).execute().data
        
        # Separate by season
        data = {
            "season1": {
                "teams": [t for t in all_teams if t['season'] == 'season1'],
                "fixtures": [f for f in all_fixtures if f['season'] == 'season1']
            },
            "season2": {
                "teams": [t for t in all_teams if t['season'] == 'season2'],
                "fixtures": [f for f in all_fixtures if f['season'] == 'season2']
            },
            "season3": {
                "teams": [t for t in all_teams if t['season'] == 'season3'],
                "fixtures": [f for f in all_fixtures if f['season'] == 'season3']
            }
        }
        
        # Fetch pending team requests
        team_requests = supabase.table('team_requests').select('*').order('created_at', desc=True).execute().data
        
    except Exception as e: # Catch specific exceptions if possible, e.g., Supabase errors
        data = {"season1": {"teams": [], "fixtures": []}, "season2": {"teams": [], "fixtures": []}, "season3": {"teams": [], "fixtures": []}}
        team_requests = []
        flash(f"Error fetching admin data: {e}", "error")
        
    return render_template('admin.html', user=session['user'], data=data, team_requests=team_requests)

@app.route('/download_fixtures/<season>')
def download_fixtures(season):
    if not supabase: return "DB Error", 500
    
    fixtures = supabase.table('fixtures').select('*').eq('season', season).order('id').execute().data
    
    from fpdf import FPDF
    from flask import Response
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt=f"Fixtures List - {season.upper()}", ln=1, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(20, 10, "Rd", 1)
    pdf.cell(70, 10, "Home Team", 1)
    pdf.cell(70, 10, "Away Team", 1)
    pdf.cell(30, 10, "Status", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=11)
    for f in fixtures:
        status = "Played" if f['status'] == 'Completed' else "Vs"
        pdf.cell(20, 10, str(f['round']), 1)
        pdf.cell(70, 10, f['home_team'], 1)
        pdf.cell(70, 10, f['away_team'], 1)
        pdf.cell(30, 10, status, 1)
        pdf.ln()
        
    return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':f'attachment;filename=fixtures_{season}.pdf'})

# --- Team Authentication & Dashboard ---
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/team/register', methods=['GET', 'POST'])
def team_register():
    if request.method == 'POST':
        email = request.form.get('email')
        team_name = request.form.get('team_name')
        password = request.form.get('password')
        
        if not email or not team_name or not password:
            flash("All fields are required", "error")
            return redirect(url_for('team_register'))
            
        # Check if team exists in Season 2 (Validation)
        # We allow registration only if team exists in teams table (case insensitive check recommended but strict here for now)
        try:
            team_exists = supabase.table('teams').select('id').eq('name', team_name).eq('season', 'season2').execute().data
            if not team_exists:
                flash(f"Team '{team_name}' not found in Season 2. Please check spelling.", "error")
                return redirect(url_for('team_register'))
                
            # Insert into team_requests table
            # NOTE: User must create this table in Supabase: 
            # create table team_requests (id uuid default gen_random_uuid() primary key, email text, password text, team_name text, status text default 'pending', created_at timestamptz default now());
            
            # Check if email already registered
            existing_user = supabase.table('team_requests').select('id').eq('email', email).execute().data
            if existing_user:
                flash("Email already registered (or pending approval).", "error")
                return redirect(url_for('team_login'))

            hashed_pw = generate_password_hash(password)
            
            supabase.table('team_requests').insert({
                'email': email,
                'team_name': team_name,
                'password': hashed_pw,
                'status': 'pending'
            }).execute()
            
            flash("Registration successful! Please wait for Admin approval.", "success")
            return redirect(url_for('team_login'))
            
        except Exception as e:
            flash(f"Error: {str(e)}. (Ensure 'team_requests' table exists)", "error")
            return redirect(url_for('team_register'))

    return render_template('register.html')

@app.route('/team/login', methods=['GET', 'POST'])
def team_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Check custom table
            user_record = supabase.table('team_requests').select('*').eq('email', email).execute().data
            
            if not user_record:
                flash("Invalid credentials or user not found.", "error")
                return redirect(url_for('team_login'))
            
            user = user_record[0]
            
            if user['status'] == 'pending':
                flash("Account is pending approval. Please contact Admin.", "error")
                return redirect(url_for('team_login'))
            elif user['status'] == 'declined':
                 flash("Account registration was declined.", "error")
                 return redirect(url_for('team_login'))
                 
            if check_password_hash(user['password'], password):
                # Login Success
                session['team_user'] = user['email']
                session['team_name'] = user['team_name']
                return redirect(url_for('team_dashboard'))
            else:
                flash("Invalid password.", "error")
                return redirect(url_for('team_login'))
                
        except Exception as e:
            flash(f"Login error: {str(e)}", "error")
            
    return render_template('team_login.html')

@app.route('/team/dashboard')
def team_dashboard():
    if 'team_user' not in session:
        return redirect(url_for('team_login'))
    
    team_name = session.get('team_name')
    
    # Reuse the logic from team_analysis but strictly for this team
    try:
        team_data = supabase.table('teams').select('*').eq('name', team_name).eq('season', 'season2').single().execute().data
        if not team_data:
            return f"Error: Team '{team_name}' data not found. Please contact admin."
            
        # Redirect to the analysis view logic using ID
        return team_analysis(team_data['id'])
        
    except Exception as e:
        return f"Error loading dashboard: {e}"

# Modified to be public or admin only? 
# The user asked for "Team Analysis" button to lead to login. 
# So '/analysis_list' is effectively replaced or guarded.
@app.route('/analysis_list') 
def analysis_list():
    # If already logged in as team, go to dashboard
    if 'team_user' in session:
        return redirect(url_for('team_dashboard'))
    # Else go to login choice
    return redirect(url_for('team_login'))

@app.route('/analysis')
def analysis_list_old(): # Renamed to avoid conflict with new analysis_list
    if not supabase:
        flash("Database connection failed", "error")
        return redirect(url_for('landing'))
    
    # Fetch all teams from Season 2
    teams = supabase.table('teams').select('*').eq('season', 'season2').order('name').execute().data
    return render_template('analysis_list.html', teams=teams)

@app.route('/analysis/<int:team_id>')
def team_analysis(team_id):
    if not supabase: return redirect(url_for('landing'))
    
    # Get season from query parameter, default to season3
    selected_season = request.args.get('season', 'season3')
    
    # 1. Get Team Details
    team = supabase.table('teams').select('*').eq('id', team_id).single().execute().data
    if not team:
        flash("Team not found", "error")
        return redirect(url_for('analysis_list'))
        
    team_name = team['name']
    season = team['season']
    
    # Check if user wants a different season view - redirect to a team in that season
    if selected_season != season:
        # Find the same team name in the selected season
        alt_team = supabase.table('teams').select('*').eq('name', team_name).eq('season', selected_season).execute().data
        if alt_team:
            return redirect(url_for('team_analysis', team_id=alt_team[0]['id'], season=selected_season))
        else:
            flash(f"{team_name} not found in {selected_season}", "warning")
            # Stay on current team but show message
    
    # 2. Get All Fixtures for this team
    # Supabase "or" syntax is a bit specific: .or_(f"home_team.eq.{team_name},away_team.eq.{team_name}")
    # But filtering by season first is good.
    # We will fetch all season fixtures and filter in python for simplicity and reliability with complex OR queries
    all_season_fixtures = supabase.table('fixtures').select('*').eq('season', season).execute().data
    
    team_fixtures = [f for f in all_season_fixtures if f['home_team'] == team_name or f['away_team'] == team_name]
    
    # 3. Analyze Fixtures
    completed_matches = [f for f in team_fixtures if f['status'] == 'Completed']
    remaining_matches = [f for f in team_fixtures if f['status'] != 'Completed']
    
    matches_played = len(completed_matches)
    matches_remaining = len(remaining_matches)
    current_points = team['points']
    max_possible_points = current_points + (matches_remaining * 3)
    
    # 4. Head-to-Head Analysis
    # Dictionary: opponent_name -> {played: 0, remaining: 0, results: []}
    h2h = {}
    
    # Get all other teams to initialize
    all_teams = supabase.table('teams').select('name').eq('season', season).execute().data
    for t in all_teams:
        if t['name'] != team_name:
            h2h[t['name']] = {'played': 0, 'remaining': 0, 'results': []}
            
    for f in team_fixtures:
        opponent = f['away_team'] if f['home_team'] == team_name else f['home_team']
        
        if opponent not in h2h: continue # Should not happen if data is consistent
        
        if f['status'] == 'Completed':
            h2h[opponent]['played'] += 1
            
            # Determine Result
            if f['home_team'] == team_name:
                h_score, a_score = f['home_score'], f['away_score']
                res = 'W' if h_score > a_score else 'L' if a_score > h_score else 'D'
            else:
                h_score, a_score = f['home_score'], f['away_score']
                res = 'W' if a_score > h_score else 'L' if h_score > a_score else 'D'
            
            h2h[opponent]['results'].append(res)
        else:
            h2h[opponent]['remaining'] += 1

    # 5. League Context (To see position)
    standings = supabase.table('teams').select('*').eq('season', season).order('points', desc=True).execute().data
    current_rank = next((i for i, t in enumerate(standings, 1) if t['id'] == team['id']), '-')
    leader_points = standings[0]['points'] if standings else 0
    points_to_leader = leader_points - current_points
    
    # 6. Get available seasons for team (for season switcher) - exclude season1
    available_seasons = []
    for s in ['season3', 'season2']:
        team_in_season = supabase.table('teams').select('id').eq('name', team_name).eq('season', s).execute().data
        if team_in_season:
            available_seasons.append(s)
    
    return render_template('analysis_detail.html', 
                         team=team,
                         matches_played=matches_played,
                         matches_remaining=matches_remaining,
                         max_possible_points=max_possible_points,
                         h2h=h2h,
                         remaining_matches=remaining_matches,
                         current_rank=current_rank,
                         leader_points=leader_points,
                         points_to_leader=points_to_leader,
                         available_seasons=available_seasons)

@app.route('/logout')
def logout():
    if 'access_token' in session:
        try:
            supabase.auth.sign_out()
        except:
            pass
    session.clear() # Clears both admin and team sessions
    return redirect(url_for('landing'))

if __name__ == '__main__':
    app.run(debug=True)
