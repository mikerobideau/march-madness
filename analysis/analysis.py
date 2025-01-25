import pandas
import numpy as np
from sklearn.metrics import log_loss

YEAR = 2025

#ENTER GAME DETAILS HERE
#-----------------------
FAVORITE = 'Iowa St.'
FAVORITE_ODDS = -550
UNDERDOG = 'Arizona St.'
UNDERDOG_ODDS = 400
HOME_TEAM = 'Arizona St.'
HOME_COURT_ADVANTAGE = 4
#-----------------------

def main():
    score = remove_d2_d3_games(pandas.read_csv('exports/2025/scores_detail.csv'))
    analyze('', score, FAVORITE, FAVORITE_ODDS, UNDERDOG, UNDERDOG_ODDS, HOME_TEAM, True)
    #validate_model(score)
    #home_court = calc_home_court_advantage(score)

def validate_model(score):
    print("Validating model...")
    sample = score.sample(n=500, random_state=21)
    outcomes = []
    p = []
    for i, game in sample.iterrows():
        result = predict(score, game)
        outcomes.append(result['is_correct'])
        p.append(result['p'])
    print("Brier: %s" % (format(brier_score(outcomes, p))))
    print("Log Loss: %s: " % (format(log_loss(outcomes, p))))

def brier_score(y_true, y_pred):
    return np.mean((np.array(y_pred) - np.array(y_true))**2)

def predict(score, game):
    team1_games = score[score['team'] == game['team']]
    team2_games = score[score['team'] == game['opponent']]
    team1_wins = 0
    team2_wins = 0
    spreads = []
    home_team = game['home_team']

    for i, game1 in team1_games.iterrows():
        for j, game2 in team2_games.iterrows():
            spread = simulate_spread(game1, game2, home_team)
            #total wins & ignore ties
            if spread < 0:
                team1_wins += 1
                spreads.append(spread)
            elif spread > 0:
                team2_wins += 1
                spreads.append(spread)

    total = team1_wins + team2_wins
    team1_p = team1_wins / total
    team2_p = team2_wins / total
    predicted_winner = 'team1' if team1_p >= team2_p else 'team2'
    actual_winner = 'team1' if game['team_score'] >= game['opponent_score'] else 'team2'
    p = team1_p if actual_winner == 'team1' else team2_p

    return {
        'team1': game['team'],
        'team2': game['opponent'],
        'predicted_winner': predicted_winner,
        'actual_winner': actual_winner,
        'is_correct': predicted_winner == actual_winner,
        'team1_p': team1_p,
        'team2_p': team2_p,
        'p': p,
        'spreads': spreads
    }

def analyze(book, score, team1, team1_odds, team2, team2_odds, home_team, print_enabled):
    team1_games = score[score['team'] == team1]
    team2_games = score[score['team'] == team2]
    spreads = []
    team1_wins = 0
    team2_wins = 0
    for i, game1 in team1_games.iterrows():
        for j, game2 in team2_games.iterrows():
            spread = simulate_spread(game1, game2, home_team)
            #total wins & ignore ties
            if spread < 0:
                team1_wins += 1
                spreads.append(spread)
            elif spread > 0:
                team2_wins += 1
                spreads.append(spread)

    team1_p = team1_wins / (team1_wins + team2_wins)
    team2_p = team2_wins / (team1_wins + team2_wins)
    team1_ev = get_ev(team1_p, team1_odds)
    team2_ev = get_ev(team2_p, team2_odds)

    row = {
        'book': book,
        'team1': team1,
        'highest_ev': team1_ev if team1_ev >= team2_ev else team2_ev,
        'team1_ev': team1_ev,
        'team1_p': team1_p,
        'team1_spread': np.median(spreads),
        'team1_book_odds': team1_odds,
        'team2': team2,
        'team2_ev': team2_ev,
        'team2_p': team2_p,
        'team2_spread': -1 * np.median(spreads),
        'team2_book_odds': team2_odds
    }

    if print_enabled:
        print('------------------------------')
        print('%s (%s)' % (team1, format_odds(team1_odds)))
        print('------------------------------')
        print('EV: %s' % (format(team1_ev)))
        print('Win probability: %s' % (format(team1_p)))
        print("Spread (Mean): %s" % (format(np.mean(spreads))))
        print("Spread (Median): %s" % (format(np.median(spreads))))
        print("Spread (SD): %s" % (format(np.std(spreads))))
        print('------------------------------')
        print('%s (%s)' % (team2, format_odds(team2_odds)))
        print('------------------------------')
        print('EV: %s' % (format(team2_ev)))
        print('Win probability: %s' % (format(team2_p)))
        print("Spread (Mean): %s" % (format(-1* np.mean(spreads))))
        print("Spread (Median): %s" % (format(-1 * np.median(spreads))))
        print("Spread (SD): %s" % (format(np.std(spreads))))

    return row

def simulate_spread(game1, game2, home_team):
    diff1 = game1['adjusted_diff'] + HOME_COURT_ADVANTAGE if game1['team'] == home_team else game1['adjusted_diff']
    diff2 = game2['adjusted_diff'] + HOME_COURT_ADVANTAGE if game2['team'] == home_team else game2['adjusted_diff']
    return diff2 - diff1

def get_ev(win_p, odds):
    loss_p = 1 - win_p
    if odds > 0:
        profit_if_win = odds
    else:
        profit_if_win = 100 / -odds * 100
    return (win_p * profit_if_win) - (loss_p * 100)

def format(stat):
    return "{:.2f}".format(stat)

def format_odds(odds):
    if odds < 0:
        return odds
    else:
        return '+%s' % (odds)

def is_same_matchup(game, game1, game2):
    return game1['opponent'] == game['opponent'] and game2['opponent'] == game['team']

def remove_d2_d3_games(score):
    #if adjusted diff is NA, game is most likely against a DII/DIII school and there was insufficient data
    return score[score['adjusted_diff'].isna() == False]

def calc_home_court_advantage(score):
    home_games = score[score['team'] == score['home_team']]
    away_games = score[score['team'] != score['home_team']]
    home_diff = np.median(home_games['adjusted_diff'])
    away_diff = np.median(away_games['adjusted_diff'])
    advantage = home_diff - away_diff
    print('Median home game adjusted diff: %s' % (home_diff))
    print('Median away game adjusted diff: %s' % (away_diff))
    print('Home court advantage: %s' % (advantage))
    return advantage

if __name__ == '__main__':
    main()