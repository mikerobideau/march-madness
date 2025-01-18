setwd('/Users/mikerobideau/Projects/march-madness/exports/2018')
bracket <- read.csv('ncaa_d1_basketball_bracket.csv', header=TRUE, stringsAsFactors=FALSE)
power_ranking <- read.csv('power_ranking.csv', header=TRUE, stringsAsFactors=FALSE)
rounds = 5

simulate <- function(team1, team2) {
  team1_diffs = get_diffs(team1)
  team2_diffs = get_diffs(team2)

  #print(team1_diffs)
  #print('---')
  #print(team2_diffs)
  
  team1_wins = 0
  team2_wins = 0
  
  for(i in 1:10000) {
    team1_diff = sample(team1_diffs, 1, replace=TRUE)
    team2_diff = sample(team2_diffs, 1, replace=TRUE)
    if(team1_diff > team2_diff) {
      team1_wins = team1_wins + 1
    } else if(team2_diff > team1_diff) {
      team2_wins = team2_wins + 1
    }
  }
    
  team1_p = team1_wins / (team1_wins + team2_wins) 
  return(team1_p)
}

get_diffs <- function(team) {
  garbage_game_spread = -15
  small_sample_cutoff = 20
  
  #ignore games against extremely weak opponents.
  diffs <- power_ranking[power_ranking$team1==team & power_ranking$spread > garbage_game_spread,]$adjusted_diff
  num_garbage_games = nrow(power_ranking[power_ranking$team1==team & power_ranking$spread < garbage_game_spread,])
  
  if(length(diffs) < small_sample_cutoff) {
    print(paste('WARNING: ', team, ' played ', num_garbage_games, ' games against weak opponents.  Using all game data'))
    diffs <- power_ranking[power_ranking$team1==team,]$adjusted_diff
  }
  
  print(paste('Using', length(diffs), ' games for', team))
  
  return(diffs)
}

survivors = bracket$team
for(round in 1:6) {
  print('---')
  print(paste('ROUND', round))
  next_round <- c()
  game_num = 1
  for(i in seq(1, (length(survivors)-1), 2)) {
    team1 = survivors[i]
    team2 = survivors[i+1]
    
    print('---')
    print(paste(team1, ' vs ', team2))
    
    team1_p = simulate(team1, team2)
    team2_p = 1 - team1_p
    if(team1_p > team2_p) {
      print(paste(team1, ' (', round(team1_p*100, 1), '%)', sep=''))
      next_round[game_num] = team1
    } else if(team2_p > team1_p) {
      print(paste(team2, ' (', round(team2_p*100, 1), '%)', sep=''))
      next_round[game_num] = team2
    } else {
      print('COINFLIP!')
      next_round[game_num] = team1
    }
    
    game_num = game_num + 1
  }
  
  survivors = next_round
  print('---')
  print('Survivors: ')
  print(next_round)
  
}

path_difficulty <- function (team, opps) {
  p = 1
  
  for(opp in opps) {
    p = p * simulate(team, opp)
  }
    
  return(p)
}
