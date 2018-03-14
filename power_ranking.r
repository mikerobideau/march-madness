#Data
setwd('~/Code/march-madness/exports/2018')
standing <- read.csv('ncaa_d1_basketball_standing.csv', header=TRUE, stringsAsFactors=FALSE)
score <- read.csv('ncaa_d1_basketball_score.csv', header=TRUE, stringsAsFactors=FALSE) 
bracket <- read.csv('ncaa_d1_backetball_bracket.csv', header=TRUE, stringsAsFactors=FALSE)

#We need a "%!in%" operation for later on
"%!in%" <- function(x,table) match(x,table, nomatch = 0) == 0

#Duplicates the dataset with team 1 and team 2 flipped, then rbinds to original.  Team 2 always mean "opponent"
mirror <- function(score) {
  mirror <- data.frame(
    record_id=score$record_id,
    year=score$year,
    team1=score$team2,
    team1_score=score$team2_score,
    team2=score$team1,
    team2_score=score$team1_score
  )
  return(rbind(mirror, score))
}

#A team's conference
conference <- function(t) {
	return(subset(standing, team==t)$conference)
}

#All teams in a conference
teamsInConference <- function(c) {
	return(subset(standing, conference==c)$team)
}

#Games against a same-conference opponent
inConferenceGames <- function(t) {
	teams <- teamsInConference(conference(t))
	games <- score[(score$team1==t & score$team2 %in% teams), ]
	return(games)
}

#Median scoring differential when playin an in conference opponent
inConferenceDiff <- function(t) { 
	diffs <- inConferenceGames(t)$team1_score - inConferenceGames(t)$team2_score
	return(median(diffs))
}

#Games against the bracket teams (TO DO: It's worth considering whether or not this should include in-conference
#opponents)
tourneyOpponentGames <- function(c) {
	games <- score[(score$team1 %in% teamsInConference(c) & score$team2 %in% bracket$team & score$team2 %!in% teamsInConference(c)), ]
	return(games)
} 

tourneyOpponentGames2 <- function(c) {
	games <- score[(score$team1 %in% teamsInConference(c) & score$team2 %in% bracket$team), ]
	return(games)
} 

outConferenceGames <- function(c) {
	games <- score[(score$team1 %in% teamsInConference(c) & score$team2 %!in% teamsInConference(c), ]
	return(games)
} 

#conferenceDiff <- function(c, recursive) {
#  if(recursive) {
#    spread = unlist(lapply(tourneyOpponentGames(c)$team2, getSpread, recursive=FALSE))
#    diffs <- tourneyOpponentGames(c)$team1_score - tourneyOpponentGames(c)$team2_score + spread
#  } else {
#    diffs <- tourneyOpponentGames(c)$team1_score - tourneyOpponentGames(c)$team2_score 
#  }
#  
#  return(median(diffs, na.rm=TRUE))
#}
#
#getSpread <- function(t, recursive) {
#	return(conferenceDiff(conference(t), recursive) + inConferenceDiff(t))
#}

#Median scoring differential for a conference when playing a tournament team
conferenceDiff <- function(c) {
  diffs <- tourneyOpponentGames(c)$team1_score - tourneyOpponentGames(c)$team2_score 
  return(median(diffs, na.rm=TRUE))
}

#Spread for one opponent
getSpread <- function(t) {
  confDiff <- conferenceDiff(conference(t))
  inConfDiff <- inConferenceDiff(t)
  return(confDiff + inConfDiff)
}

#Spread for each opponent in standings
getAllSpread <- function() {
  spread <- sapply(standing$team, getSpread)
  df <- data.frame(team2=names(spread), spread=spread)
  return(df)
}

#Adjusts scoring differentials based on opponent spread.  Re-calcuates opponent spread based on their scoring differentials, and repeats
#for a specified number of iterations
iterAdjust <- function(iterations) {
  for(i in 0:iterations){
    if(i==0) {
      allSpread <- getAllSpread() #for first iteration, use approximated spread
    } else {
      allSpread <- getAllMedianAdjustedDiff() #for all other iterations, spread is median scoring differential from previous iteration
    }
  
    merged <- merge(score, allSpread, by='team2')
  
    adjusted <- cbind(
      merged, adjusted_diff = merged$team1_score - merged$team2_score + merged$spread
    )
  
    medianAdjustedDiff <- function(t) {
      return(median(subset(adjusted, team1==t)$adjusted_diff, na.rm=T))
    }
  
    getAllMedianAdjustedDiff <- function() {
      spread <- sapply(standing$team, medianAdjustedDiff)
      df <- data.frame(team2=names(spread), spread=spread)
      return(df)
    }
  }
  
  return(adjusted)
}


#Run script
run <- function() {
  score <- mirror(score)
  
  adjusted <- iterAdjust(1)
  
  write.csv(adjusted, 'power_ranking.csv')
}

run()