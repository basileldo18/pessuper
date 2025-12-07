// --- 1. DATA STRUCTURE (DYNAMIC) ---

let leagueData = {
    season1: { teams: [], fixtures: [] },
    season2: { teams: [], fixtures: [] }
};

if (window.leagueDataBackend) {
    // Adapter to convert DB snake_case to JS properties
    const backendData = window.leagueDataBackend;

    const processTeams = (teams) => {
        return teams.map(t => ({
            name: t.name,
            P: t.played,
            W: t.won,
            D: t.drawn,
            L: t.lost,
            GF: t.gf,
            GA: t.ga,
            Pts: t.points,
            Form: t.form,
            GD: t.gf - t.ga
        }));
    };

    const processFixtures = (fixtures) => {
        return fixtures.map(f => ({
            fixtureNum: isNaN(f.round) ? f.round : parseInt(f.round),
            date: f.date,
            time: f.time,
            home: f.home_team,
            away: f.away_team,
            venue: f.venue,
            result: (f.home_score !== null && f.away_score !== null) ? `${f.home_score} - ${f.away_score}` : "",
            status: f.status
        }));
    };

    if (backendData.season1) {
        leagueData.season1.teams = processTeams(backendData.season1.teams);
        leagueData.season1.fixtures = processFixtures(backendData.season1.fixtures);
    }
    if (backendData.season2) {
        leagueData.season2.teams = processTeams(backendData.season2.teams);
        leagueData.season2.fixtures = processFixtures(backendData.season2.fixtures);
    }
} else {
    console.error("No backend data found. Initializing empty.");
}


// --- DATA STATE & CURRENT SEASON ---
let currentSeason = 'season2';

// --- LOGIC FUNCTIONS ---

const getSortedTeams = (season) => {
    const data = leagueData[season];
    if (!data || data.teams.length === 0) return [];

    return data.teams
        .map(team => {
            // Priority: Use DB Points if available, else calculate
            const Pts = team.Pts !== undefined ? team.Pts : (team.W * 3) + team.D;
            const GD = team.GF - team.GA;
            return { ...team, Pts, GD };
        })
        .sort((a, b) => {
            // 1. Points
            if (b.Pts !== a.Pts) return b.Pts - a.Pts;
            // 2. Goal Difference
            if (b.GD !== a.GD) return b.GD - a.GD;
            // 3. Goals For (GF)
            return b.GF - a.GF;
        });
};

// Function to render the Points Table
const renderPointsTable = (season) => {
    const targetId = season === 'season1' ? 'points-table-body' : 'points-table-body-s2';
    const tableBody = document.getElementById(targetId);
    const championBanner = document.getElementById('season1-champion-banner');

    if (!tableBody) return;

    const sortedTeams = getSortedTeams(season);
    tableBody.innerHTML = '';

    if (sortedTeams.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="11" style="text-align:center; padding: 20px;">No teams data available for this season yet.</td></tr>';
        return;
    }

    sortedTeams.forEach((team, index) => {
        const row = document.createElement('tr');
        const formString = team.Form || '';
        // Only show the last 5 results
        const formResults = formString.slice(-5).toUpperCase();

        const formHTML = formResults.split('').map(result => {
            const className = result === 'W' ? 'form-win' : result === 'D' ? 'form-draw' : 'form-loss';
            return `<span class="${className}">${result}</span>`;
        }).join('');

        if (season === 'season2') {
            if (index === 0) row.classList.add('row-final');
            if (index === 1 || index === 2) row.classList.add('row-semi');
        }

        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${team.name}</td>
            <td class="stat">${team.P}</td>
            <td class="stat">${team.W}</td>
            <td class="stat">${team.D}</td>
            <td class="stat">${team.L}</td>
            <td class="stat">${team.GF}</td>
            <td class="stat">${team.GA}</td>
            <td class="stat">${team.GD > 0 ? '+' : ''}${team.GD}</td>
            <td class="points">${team.Pts}</td>
            <td class="stat form-col">${formHTML}</td>
        `;
        tableBody.appendChild(row);
    });

    // Show Champion Banner for Season 1 only
    if (season === 'season1' && championBanner) {
        championBanner.classList.remove('hidden');
    }
};

// Function to render the Fixtures
// Function to render the Fixtures
const renderFixtures = (season) => {
    const targetId = season === 'season1' ? 'fixtures-list' : 'fixtures-list-s2';
    const fixturesList = document.getElementById(targetId);

    if (!fixturesList) return;

    fixturesList.innerHTML = '';

    if (!leagueData[season] || !leagueData[season].fixtures || leagueData[season].fixtures.length === 0) {
        fixturesList.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">No fixtures scheduled yet.</div>';
        return;
    }

    const groupedFixtures = leagueData[season].fixtures.reduce((acc, fixture) => {
        // Handle both DB 'round' and legacy 'fixtureNum'
        const roundVal = fixture.round || fixture.fixtureNum;

        // Determine header key
        let key = `Matchday ${roundVal}`;
        if (['SF1', 'SF2', 'Final'].includes(String(roundVal))) {
            key = 'Knockout Stage';
        }

        if (!acc[key]) {
            acc[key] = {
                header: key,
                matches: []
            };
        }
        acc[key].matches.push(fixture);
        return acc;
    }, {});

    for (const key in groupedFixtures) {
        const group = groupedFixtures[key];

        const header = document.createElement('h3');
        header.textContent = key === 'Knockout Stage' ? 'Knockout Stage 👑 (SF & Final)' : group.header;
        fixturesList.appendChild(header);

        group.matches.forEach(fixture => {
            const card = document.createElement('div');
            let cardClass = 'fixture-card';

            const roundVal = String(fixture.round || fixture.fixtureNum);

            if (['SF1', 'SF2', 'Final'].includes(roundVal)) {
                cardClass += ' knockout';
            }
            if (fixture.status === 'Completed') {
                cardClass += ' completed';
            }

            card.classList.add(...cardClass.split(' '));

            // Map DB columns to display
            const homeTeam = fixture.home_team || fixture.home;
            const awayTeam = fixture.away_team || fixture.away;

            // Score handling
            let resultDisplay;
            if (fixture.home_score !== null && fixture.home_score !== undefined) {
                resultDisplay = `<span class="score-result">${fixture.home_score} - ${fixture.away_score}</span>`;
            } else if (fixture.result) {
                resultDisplay = `<span class="score-result">${fixture.result}</span>`;
            } else {
                resultDisplay = `<span class="vs-text">vs</span>`;
            }

            // Time/Date/Venue Placeholders if missing
            const timeDisplay = fixture.time ? (fixture.time === 'FT' ? 'FULL TIME' : fixture.time) : (fixture.status === 'Completed' ? 'FULL TIME' : 'TBD');
            const date = fixture.date || 'Upcoming';
            const venue = fixture.venue ? fixture.venue.toUpperCase() : 'PES LEAGUE STADIUM';
            const venueDisplay = fixture.status === 'Completed' ? timeDisplay : venue;

            card.innerHTML = `
                <span class="date-time">${date} / ${timeDisplay}</span>
                <div class="match-details">
                    <span class="team-name">${homeTeam}</span>
                    ${resultDisplay}
                    <span class="team-name">${awayTeam}</span>
                </div>
                <span class="stadium">${venueDisplay}</span>
            `;
            fixturesList.appendChild(card);
        });
    }
};

// --- RENDER TOP SCORERS ---
const renderTopScorers = (season) => {
    const targetId = season === 'season1' ? 'top-scorers-list' : 'top-scorers-list-s2';
    const scorersList = document.getElementById(targetId);

    if (!scorersList) return;

    // Only render if teams exist
    if (!leagueData[season] || leagueData[season].teams.length === 0) {
        scorersList.innerHTML = '<div style="text-align: center; padding: 20px;">No stats available.</div>';
        return;
    }

    const teams = leagueData[season].teams;
    const sortedScorers = [...teams].sort((a, b) => b.GF - a.GF);

    scorersList.innerHTML = '';

    sortedScorers.forEach((team, index) => {
        const listItem = document.createElement('li');

        // Add an emoji based on rank
        let rankIcon = '';
        if (index === 0) rankIcon = '🥇';
        else if (index === 1) rankIcon = '🥈';
        else if (index === 2) rankIcon = '🥉';
        else rankIcon = '⚫';

        listItem.innerHTML = `
            <span class="scorer-rank">${rankIcon} ${index + 1}.</span>
            <span class="scorer-name">${team.name}</span>
            <span class="scorer-goals">${team.GF} Goals</span>
        `;

        scorersList.appendChild(listItem);
    });
};


// Function to switch between main tabs (Table/Fixtures/Scorers)
const switchContentSection = (targetId) => {
    const currentSeasonDiv = document.getElementById(currentSeason + '-data');

    // Need to select buttons and sections within the current season's main container
    const navButtons = document.querySelectorAll('.nav-button');
    const contentSections = document.querySelectorAll('.content-section');

    navButtons.forEach(button => button.classList.remove('active'));
    contentSections.forEach(section => {
        // Check if the section belongs to the active season block before hiding
        if (section.closest(`#${currentSeason}-data`)) {
            section.classList.add('hidden');
            section.style.opacity = '0';
            section.style.animation = 'none';
        }
    });

    const activeNavButton = document.querySelector(`.nav-button[data-target="${targetId}"]`);
    if (activeNavButton) {
        activeNavButton.classList.add('active');
    }

    // Determine the actual section ID based on season and target
    let targetSectionId = targetId;
    if (currentSeason === 'season2') {
        // Special handling for Season 2 IDs
        if (targetId === 'points-table-section') targetSectionId = 'points-table-section-s2';
        else if (targetId === 'fixtures-section') targetSectionId = 'fixtures-section-s2';
        else if (targetId === 'top-scorers-section') targetSectionId = 'top-scorers-section-s2';
    }

    let targetSection = document.getElementById(targetSectionId);

    if (targetSection) {
        targetSection.classList.remove('hidden');
        setTimeout(() => {
            targetSection.style.animation = 'fadeIn 0.6s ease forwards';
        }, 50);
    }
};

// Function to switch between seasons
const switchSeason = (season) => {
    if (currentSeason === season) return;

    // Hide the old season data container
    document.getElementById(currentSeason + '-data').classList.add('hidden');
    document.querySelector(`.season-button[data-season="${currentSeason}"]`).classList.remove('active');

    currentSeason = season;

    // Show the new season data container
    document.getElementById(currentSeason + '-data').classList.remove('hidden');
    document.querySelector(`.season-button[data-season="${currentSeason}"]`).classList.add('active');

    // Re-render data for the new season
    renderPointsTable(season);
    renderFixtures(season);
    renderTopScorers(season);

    // Reset main tab to League Table
    switchContentSection('points-table-section');
};


// --- INITIALIZATION AND INTERACTIVITY ---

const initializeSite = () => {
    const navButtons = document.querySelectorAll('.nav-button');
    const seasonButtons = document.querySelectorAll('.season-button');

    navButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            const target = event.target.getAttribute('data-target');
            switchContentSection(target);
        });
    });

    seasonButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            const target = event.target.getAttribute('data-season');
            switchSeason(target);
        });
    });

    // Initial setup for Season 2
    renderPointsTable('season2');
    renderFixtures('season2');
    renderTopScorers('season2');

    // Also render Season 1 so it's ready when switched
    renderPointsTable('season1');
    renderFixtures('season1');
    renderTopScorers('season1');

    // Ensure Season 1 content is hidden initially
    const s1Data = document.getElementById('season1-data');
    if (s1Data) s1Data.classList.add('hidden');

    // Ensure Season 2 content is visible default
    const s2Data = document.getElementById('season2-data');
    if (s2Data) s2Data.classList.remove('hidden');

    // Set initial active content tab (League Table)
    switchContentSection('points-table-section');
};

document.addEventListener('DOMContentLoaded', initializeSite);
