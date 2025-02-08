USE MIKE_ROBIDEAU;

SET sql_safe_updates = 0;

#ALTER TABLE ncaa_d1_basketball_conference
#ADD COLUMN strength VARCHAR(20);

CREATE TEMPORARY TABLE avg_performance AS (
	SELECT 
			team1 AS team,
			AVG(performance_score) AS avg_performance_score
		FROM ncaa_d1_basketball_performance
		WHERE year = 2023
		GROUP BY team1
);

UPDATE ncaa_d1_basketball_conference, avg_performance
SET ncaa_d1_basketball_conference.strength = avg_performance.avg_performance_score
WHERE ncaa_d1_basketball_conference.team = avg_performance.team
AND ncaa_d1_basketball_conference.year = 2023;