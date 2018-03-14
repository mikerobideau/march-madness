SET SQL_SAFE_UPDATES = 0;

SELECT * 
FROM 
	ncaa_d1_basketball_bracket bracket
LEFT JOIN 
	ncaa_d1_basketball_standing standing ON standing.team = bracket.team
WHERE standing.year is null;

SELECT * FROM ncaa_d1_basketball_standing WHERE team like '%Texas%';
SELECT * FROM ncaa_d1_basketball_score WHERE team1 like '%Texas%';

UPDATE ncaa_d1_basketball_standing 
SET team = 'Loyola Chicago'
WHERE team = 'Loyola (IL)';

UPDATE ncaa_d1_basketball_standing 
SET team = 'CSU Fullerton'
WHERE team = 'Cal State Fullerton';

UPDATE ncaa_d1_basketball_standing 
SET team = 'Ohio St.'
WHERE team = 'Ohio State';

UPDATE ncaa_d1_basketball_standing 
SET team = 'South Dakota St.'
WHERE team = 'South Dakota State';

UPDATE ncaa_d1_basketball_bracket
SET team = 'Texas A&M'
WHERE team = 'Texas A&M;';

UPDATE ncaa_d1_basketball_standing
SET team = 'Penn'
WHERE team = 'Pennsylvania';

UPDATE ncaa_d1_basketball_standing
SET team = 'NC State'
WHERE team = 'North Carolina State';

UPDATE ncaa_d1_basketball_standing
SET team = 'New Mexico St.'
WHERE team = 'New Mexico State';

UPDATE ncaa_d1_basketball_standing
SET team = 'Mich. St.'
WHERE team = 'Michigan State';

UPDATE ncaa_d1_basketball_standing
SET team = 'UNCG'
WHERE team = 'UNC Greensboro';

UPDATE ncaa_d1_basketball_bracket
SET team = 'Syracuse'
WHERE team = 'ASU/SYR';

UPDATE ncaa_d1_basketball_bracket
SET team = 'Texas Southern'
WHERE team = 'NCC/TSU';