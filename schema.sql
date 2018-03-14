SET SQL_SAFE_UPDATES = 0;

SELECT * 
FROM 
	ncaa_d1_basketball_bracket bracket
LEFT JOIN 
	ncaa_d1_basketball_standing standing ON standing.team = bracket.team
WHERE standing.year is null;

SELECT * FROM ncaa_d1_basketball_standing WHERE team like '%Fuller%';
SELECT * FROM ncaa_d1_basketball_score WHERE team1 like '%Fuller%';

UPDATE ncaa_d1_basketball_standing 
SET team = 'Loyola Chicago'
WHERE team = 'Loyola (IL)';

UPDATE ncaa_d1_basketball_standing 
SET team = 'CSU Fullerton'
WHERE team = 'Cal State Fullerton'