// --- 1. DATA STRUCTURE (DYNAMIC) ---

let leagueData = {
    season1: { teams: [], fixtures: [] },
    season2: { teams: [], fixtures: [] },
    season3: { teams: [], fixtures: [] }
};

if (window.leagueDataBackend) {
    const backendData = window.leagueDataBackend;
    console.log("Backend Data Loaded:", backendData);

    const processTeams = (teams) => {
        return teams.map(t => ({
            name: t.name,
            played: t.played,
            won: t.won,
            drawn: t.drawn,
            lost: t.lost,
            gf: t.gf || 0,
            ga: t.ga || 0,
            points: t.points,
            form: t.form,
            gd: (t.gf || 0) - (t.ga || 0)
        }));
    };

    const processFixtures = (fixtures) => {
        return fixtures.map(f => ({
            round: f.round || f.fixtureNum,
            date: f.date,
            time: f.time,
            home: f.home_team,
            away: f.away_team,
            venue: f.venue,
            home_score: f.home_score,
            away_score: f.away_score,
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
    if (backendData.season3) {
        leagueData.season3.teams = processTeams(backendData.season3.teams);
        leagueData.season3.fixtures = processFixtures(backendData.season3.fixtures);
    }
} else {
    console.error("No backend data found! Check window.leagueDataBackend");
}

let currentSeason = 'season3';

// --- LOGIC FUNCTIONS ---

const getSortedTeams = (season) => {
    const data = leagueData[season];
    if (!data || !data.teams) return [];

    return data.teams.sort((a, b) => {
        if (b.points !== a.points) return b.points - a.points;
        if (b.gd !== a.gd) return b.gd - a.gd;
        return b.gf - a.gf;
    });
};

// Render Points Table
const renderPointsTable = (season) => {
    let targetId = 'points-table-body';
    if (season === 'season2') targetId = 'points-table-body-s2';
    if (season === 'season3') targetId = 'points-table-body-s3';

    const tableBody = document.getElementById(targetId);
    if (!tableBody) return;

    tableBody.innerHTML = '';
    const teams = getSortedTeams(season);

    if (teams.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="11" style="text-align:center; padding: 20px;">No Data Available</td></tr>';
        return;
    }

    teams.forEach((team, index) => {
        const row = document.createElement('tr');

        // Highlight logic (Season 2 only for now, can extend to S3 if rules same)
        if (season === 'season2') {
            if (index === 0) row.classList.add('row-final');
            else if (index === 1 || index === 2) row.classList.add('row-semi');
        }

        // Form HTML
        const formStr = (team.form || '').slice(-5).toUpperCase();
        const formDots = formStr.split('').map(char => {
            let cls = char === 'W' ? 'win' : char === 'D' ? 'draw' : 'loss';
            return `<div class="dot ${cls}">${char}</div>`;
        }).join('');

        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${team.name}</td>
            <td>${team.played}</td>
            <td>${team.won}</td>
            <td>${team.drawn}</td>
            <td>${team.lost}</td>
            <td>${team.gf}</td>
            <td>${team.ga}</td>
            <td>${team.gd > 0 ? '+' : ''}${team.gd}</td>
            <td class="points-cell">${team.points}</td>
            <td><div class="form-dots">${formDots}</div></td>
        `;
        tableBody.appendChild(row);
    });
};

// Render Fixtures
const renderFixtures = (season) => {
    let targetId = 'fixtures-list';
    if (season === 'season2') targetId = 'fixtures-list-s2';
    if (season === 'season3') targetId = 'fixtures-list-s3';

    const container = document.getElementById(targetId);
    if (!container) return;

    container.innerHTML = '';
    const fixtures = leagueData[season].fixtures;

    if (!fixtures || fixtures.length === 0) {
        container.innerHTML = '<div style="text-align:center; padding:20px; color:#aaa;">No Fixtures</div>';
        return;
    }

    // Group by Matchday/Round
    const groups = {};
    fixtures.forEach(f => {
        let key = `Matchday ${f.round}`;
        if (['SF1', 'SF2', 'Final'].includes(String(f.round))) key = 'Knockout Stage';

        if (!groups[key]) groups[key] = [];
        groups[key].push(f);
    });

    for (const [groupName, matches] of Object.entries(groups)) {
        const header = document.createElement('h3');
        header.style.cssText = "font-size: 1rem; color: var(--brand-accent); margin: 20px 0 10px; border-bottom: 2px solid #eee; padding-bottom: 5px;";
        header.textContent = groupName;
        container.appendChild(header);

        matches.forEach(m => {
            const card = document.createElement('div');
            card.className = 'fixture-card';
            if (m.status === 'Completed') card.classList.add('completed');

            const scoreDisplay = (m.home_score !== null && m.away_score !== null)
                ? `<span class="score-badge">${m.home_score} - ${m.away_score}</span>`
                : `<span class="vs-badge">VS</span>`;

            card.innerHTML = `
                <div class="team-block" style="text-align: right;">
                    <span class="team-name">${m.home}</span>
                </div>
                <div style="margin: 0 15px; display:flex; flex-direction:column; align-items:center;">
                    ${scoreDisplay}
                    <div style="font-size:0.7rem; color:#94a3b8; margin-top:4px; font-weight:600;">${m.status === 'Completed' ? 'FT' : (m.date || 'UPCOMING')}</div>
                </div>
                <div class="team-block" style="text-align: left;">
                    <span class="team-name">${m.away}</span>
                </div>
            `;
            container.appendChild(card);
        });
    }
};

// Render Scorers
const renderScorers = (season) => {
    let targetId = 'top-scorers-list';
    if (season === 'season2') targetId = 'top-scorers-list-s2';
    if (season === 'season3') targetId = 'top-scorers-list-s3';

    const container = document.getElementById(targetId);
    if (!container) return;

    container.innerHTML = '';
    const teams = leagueData[season].teams;
    if (!teams || teams.length === 0) {
        container.innerHTML = '<div style="text-align:center; padding:20px;">No Data</div>';
        return;
    }

    // Sort by GF (Proxy for scorers since we don't track player goals individually yet)
    const sorted = [...teams].sort((a, b) => b.gf - a.gf);

    sorted.forEach((t, i) => {
        const div = document.createElement('div');
        div.className = 'scorer-item';

        let rankIcon = '';
        if (i === 0) rankIcon = '🥇';
        else if (i === 1) rankIcon = '🥈';
        else if (i === 2) rankIcon = '🥉';
        else rankIcon = `#${i + 1}`;

        div.innerHTML = `
            <span class="scorer-rank">${rankIcon}</span>
            <span class="scorer-info">${t.name}</span>
            <span class="scorer-goals">${t.gf} G</span>
        `;
        container.appendChild(div);
    });
};

// --- INITIALIZE ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("Initializing App...");

    // 1. Render All Data
    renderPointsTable('season3');
    renderFixtures('season3');
    renderScorers('season3');

    renderPointsTable('season2');
    renderFixtures('season2');
    renderScorers('season2');

    renderPointsTable('season1');
    renderFixtures('season1');
    renderScorers('season1');

    // 2. Setup Tab Listeners
    const seasonBtns = document.querySelectorAll('.season-button');
    const navBtns = document.querySelectorAll('.nav-button');
    const s1Data = document.getElementById('season1-data');
    const s2Data = document.getElementById('season2-data');
    const s3Data = document.getElementById('season3-data');

    // Handle Season Switch
    seasonBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // UI Toggle
            seasonBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Logic
            currentSeason = btn.dataset.season;

            // Hide all
            if (s1Data) s1Data.classList.add('hidden');
            if (s2Data) s2Data.classList.add('hidden');
            if (s3Data) s3Data.classList.add('hidden');

            // Show current
            if (currentSeason === 'season1' && s1Data) s1Data.classList.remove('hidden');
            else if (currentSeason === 'season2' && s2Data) s2Data.classList.remove('hidden');
            else if (currentSeason === 'season3' && s3Data) s3Data.classList.remove('hidden');

            // Reset to Table view when switching season
            navBtns[0].click();
        });
    });

    // Handle Content Switch (Table/Fixtures/Scorers)
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // UI Toggle
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Logic
            const targetBase = btn.dataset.target; // e.g. "points-table-section"

            let container;
            if (currentSeason === 'season1') container = s1Data;
            else if (currentSeason === 'season2') container = s2Data;
            else container = s3Data;

            if (!container) return;

            // Hide all sections in current container
            container.querySelectorAll('.content-section').forEach(sec => sec.classList.add('hidden'));

            // Construct specific ID based on convention: generic-id + "-s1", "-s2", or "-s3"
            let suffix = '-s1';
            if (currentSeason === 'season2') suffix = '-s2';
            if (currentSeason === 'season3') suffix = '-s3';

            const specificId = targetBase + suffix;

            const targetSection = document.getElementById(specificId);
            if (targetSection) {
                targetSection.classList.remove('hidden');
            } else {
                console.warn("Target section not found:", specificId);
            }
        });
    });
});
