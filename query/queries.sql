USE march_madness;


-- This is the important one.
-- Make sure every conference team is in the score table.
-- If they are not, there is probably some inconsistency in how the name is written, e.g., "St Marys" vs "Saint Marys"
SELECT DISTINCT team FROM ncaa_d1_basketball_conference
WHERE team IN (
	SELECT DISTINCT team1 FROM ncaa_d1_basketball_score
);

-- These mismatches shouldn't matter.  These should all be D2 and D3 teams.
SELECT DISTINCT team1 FROM ncaa_d1_basketball_score
WHERE team1 NOT IN (
	SELECT DISTINCT team FROM ncaa_d1_basketball_conference
);

-- Once cleanup is done, get the D1 scores
SELECT * FROM ncaa_d1_basketball_score
WHERE year = '2022'
	AND team1 IN (SELECT team FROM ncaa_d1_basketball_conference)
    AND team2 IN (SELECT team FROM ncaa_d1_basketball_conference);
