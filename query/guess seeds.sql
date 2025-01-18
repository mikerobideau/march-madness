USE MIKE_ROBIDEAU;

#avg of performance score
SELECT 
	ROW_NUMBER() OVER() AS num_row,
	team,
    avg_performance_score
FROM (
	SELECT 
		team1 AS team,
		AVG(performance_score) AS avg_performance_score
	FROM ncaa_d1_basketball_performance
	WHERE year = 2023
	GROUP BY team1
) avg_performance
ORDER BY avg_performance_score DESC;