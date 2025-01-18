CREATE SCHEMA march_madness;

USE march_madness;

CREATE TABLE ncaa_d1_basketball_bracket (
	year INT,
    team VARCHAR(100),
    PRIMARY KEY (year, team)
);

CREATE TABLE ncaa_d1_basketball_score (
	year INT,
    team1 VARCHAR(100),
    team1_score INT,
	team2 VARCHAR(100),
    team2_score INT
);

CREATE TABLE ncaa_d1_basketball_conference (
	year INT,
    team VARCHAR(100),
	conference VARCHAR(100),
    PRIMARY KEY (year, team, conference)
);