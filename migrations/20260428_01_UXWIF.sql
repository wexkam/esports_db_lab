CREATE TABLE team (
    team_id SERIAL PRIMARY KEY,
    title VARCHAR(255) UNIQUE NOT NULL,
    coach VARCHAR(255),
    region VARCHAR(100),
    foundation_date DATE
);

CREATE TABLE player (
    player_id SERIAL PRIMARY KEY,
    nickname VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(100)
);

CREATE TABLE match (
    match_id SERIAL PRIMARY KEY,
    team_id INT REFERENCES team(team_id) ON DELETE CASCADE,
    match_code VARCHAR(50) UNIQUE NOT NULL,
    stage VARCHAR(100),
    result_1 INT DEFAULT 0,
    result_2 INT DEFAULT 0,
    maps TEXT
);

CREATE TABLE player_team (
    player_id INT REFERENCES player(player_id) ON DELETE CASCADE,
    team_id INT REFERENCES team(team_id) ON DELETE CASCADE,
    join_date DATE NOT NULL,
    departure_date DATE,
    PRIMARY KEY (player_id, team_id, join_date)
);
