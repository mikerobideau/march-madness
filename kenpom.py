from kenpompy.utils import login
import statsmodels.api as sm
import kenpompy.summary as kp
import pandas
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import os
import json

import fuzzy

YEAR = '2025'
TEST_START_DATE = pandas.Timestamp(f"{YEAR}-01-01")
TEST_END_DATE = pandas.Timestamp(f"{YEAR}-01-31")
TEST_DATES = pandas.date_range(start=TEST_START_DATE, end=TEST_END_DATE, freq="D")
TEST_BOOK = 'fanduel'
USER = 'kingrobideau@gmail.com'
PASSWORD = 'Devdev77!'
DIR = 'exports/%s/kenpom' % (YEAR)
HISTORICAL_DIR = 'exports/odds_historical'

def run():
    odds = load_odds()
    print(odds)
    #model = logit()
    #p = win_prob('Vermont', 'Duke', model)
    #print(p)

def prepare_game_data():
    #game scores
    df = load_scores()
    df['home_win'] = df['diff'].apply(lambda x: 1 if x < 0 else 0) #diff is negative when home team wins
    #df['is_home'] = (df['team'] == df['home_team']).astype(int)
    weights = pandas.read_csv('exports/%s/weights.csv' % (YEAR))
    weights = weights.rename(columns={'Score': 'Weight'})

    #merge away team stats
    away_weights = weights.add_prefix('away_')
    print(away_weights.columns)
    df = df.merge(away_weights, left_on='team', right_on='away_Team', how='inner')
    ff = load('four_factors')
    away_ff = ff.add_prefix('away_')
    df = df.merge(away_ff, left_on='team', right_on='away_Team', how='inner')
    #eff = load('efficiency')
    #away_eff = eff.add_prefix('away_')
    #df = df.merge(away_eff, left_on='team', right_on='away_Team', how='inner')

    #merge home team stats
    home_weights = weights.add_prefix('home_')
    df = df.merge(home_weights, left_on='opponent', right_on='home_Team', how='inner')
    home_ff = ff.add_prefix('home_')
    df = df.merge(home_ff, left_on='opponent', right_on='home_Team', how='inner')
    #eff = load('efficiency')
    #home_eff = eff.add_prefix('home_')
    #df = df.merge(home_eff, left_on='team', right_on='home_Team', how='inner')

    #odds
    pandas.read_csv('exports/%s')

    #calculated fields
    df['away_team'] = df['team']
    df['home_team'] = df['opponent']
    df['away_AdjE'] = df['away_AdjOE'] - df['away_AdjDE']
    df['home_AdjE'] = df['home_AdjOE'] - df['home_AdjDE']
    df['favorite'] = df.apply(lambda row: row.home_team if row.home_AdjE > row.away_AdjE else row.away_team, axis=1)
    df['underdog'] = df.apply(lambda row: row.home_team if row.away_team == row.favorite else row.away_team, axis=1)
    df['winner'] = df.apply(lambda row: row.home_team if row.home_win else row.away_team, axis=1)
    df['underdog_win'] = df.apply(lambda row: 1 if row.favorite != row.winner else 0, axis=1)
    df['predicted_spread'] = (df['home_AdjE'] - df['away_AdjE']) * (df['home_AdjTempo'] + df['away_AdjTempo']) / 200 #200 because tempo is based on 100 possessions, and we have two teams
    #df['weight_diff'] = df['home_Weight'] - df['away_Weight']
    df['tempo'] = (df['home_AdjTempo'] + df['away_AdjTempo']) / 2
    df['favorite_tempo'] = df.apply(lambda row: row.home_AdjTempo if row.favorite == row.home_team else row.away_AdjTempo, axis=1)
    df['underdog_tempo'] = df.apply(lambda row: row.home_AdjTempo if row.favorite == row.away_team else row.away_AdjTempo, axis=1)
    df['underdog_is_home'] = df.apply(lambda row: 1 if row.underdog == row.home_team else 0, axis=1)
    

    #subset columns
    #df = df[['home_win', 'away_Weight', 'away_AdjE', 'away_AdjTempo', 'away_Off-eFG%', 'away_Off-TO%', 'away_Off-OR%', 'away_Off-FTRate', 'away_Def-eFG%', 'away_Def-TO%', 'away_Def-OR%', 'away_Def-FTRate',
    #         'home_Weight', 'home_AdjE', 'home_AdjTempo', 'home_Off-eFG%', 'home_Off-TO%', 'home_Off-OR%', 'home_Off-FTRate', 'home_Def-eFG%', 'home_Def-TO%', 'home_Def-OR%', 'home_Def-FTRate']]

    df = df[['underdog_win', 'favorite_tempo', 'underdog_tempo', 'underdog_is_home']]

    return df

def load_odds():
    odds_output_data = []
    for date in TEST_DATES:
        historical_file_path = os.path.join(HISTORICAL_DIR, ('odds-%s.json' % date.strftime('%Y-%m-%d')))
        with open(historical_file_path, 'r') as json_file:
            data = json.load(json_file)
        for game in data['data']:
            for bookmaker in game['bookmakers']:
                book = bookmaker['key']
                if book == TEST_BOOK:
                    for market in bookmaker['markets']:
                        if market['key'] == 'h2h':
                            outcomes = pandas.DataFrame(market['outcomes'])
                            outcome1 = outcomes.iloc[0]
                            outcome2 = outcomes.iloc[1]
                            away_team_odds = outcome1['price'] if outcome1['name'] == game['away_team'] else outcome2['price']
                            home_team_odds = outcome1['price'] if outcome1['name'] == game['home_team'] else outcome2['price']
                            away_team_school = fuzzy.map(game['away_team'])
                            home_team_school = fuzzy.map(game['home_team'])
                            row = {'data': date, 'away_team': away_team_school, 'away_team_odds': away_team_odds, 'home_team': home_team_school, 'home_team_odds': home_team_odds}
                            print(row)
                            odds_output_data.append(row)
    return pandas.DataFrame(odds_output_data)

def prepare_team_data():
    ff = load('four_factors')
    return ff

def logit():
    df = prepare_game_data()

    X = df.drop(columns=['underdog_win'])
    #X = df[['away_Weight', 'home_Weight']]
    y = df['underdog_win']

    X = sm.add_constant(X)
    model = sm.Logit(y, X).fit()

    print('==============================================================================')
    print('MODEL TRAINED TO FIT A HOME TEAM WIN')
    print('==============================================================================')
    print(model.summary())

    return model

def random_forest():
    df = prepare_game_data()
    X = df.drop(columns=['underdog_win'])
    y = df['underdog_win']

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    feature_importances = pandas.DataFrame({'Feature': X.columns, 'Importance': model.feature_importances_})
    print(feature_importances.sort_values(by='Importance', ascending=False))
    print(f"Training Accuracy: {model.score(X, y):.4f}")

#calculates probability of away team winning, home team losing
def win_prob(away, home, model):
    df = prepare_team_data()
    away_stats = df[df['Team'] == away][['AdjOE', 'AdjDE']].values
    home_stats = df[df['Team'] == home][['AdjOE', 'AdjDE']].values
    #df = pandas.read_csv('exports/%s/weights.csv' % (YEAR))
    #away_stats = df[df['Team'] == away][['Score']].values
    #home_stats = df[df['Team'] == home][['Score']].values
    #if len(away_stats) == 0 or len(home_stats) == 0:
    #    raise ValueError("Team or Opponent not found in dataset.")

    matchup_features = np.hstack([away_stats.flatten(), home_stats.flatten()])

    matchup_features = np.insert(matchup_features, 0, 1)  # Adds '1' as the first element to match model shape (5,)

    log_odds = model.predict(matchup_features.reshape(1, -1))
    p = sigmoid(log_odds)[0]

    return p

def sigmoid(x):
    return 1 / (1 + np.exp(-x))  # Converts log-odds to probability


def load_scores():
    df = pandas.read_csv('exports/%s/scores_detail.csv' % (YEAR))
    return df[df['home_team'] == df['opponent']]

def scrape():
    print('logging in')
    browser = login(USER, PASSWORD)
    print('downloading efficiency')
    eff_stats = kp.get_efficiency(browser)
    eff_stats.to_csv('%s/efficiency.csv' % (DIR))
    print('downloading four factors')
    four_factors = kp.get_fourfactors(browser)
    four_factors.to_csv('%s/four_factors.csv' % (DIR))
    print('downloading point distribution')
    point_dist = kp.get_pointdist(browser)
    point_dist.to_csv('%s/point_dist.csv' % (DIR))
    print('downloading team stats')
    team_stats = kp.get_teamstats(browser)
    team_stats.to_csv('%s/team_stats.csv' % (DIR))
    print('downloading height and experience')
    height_exp = kp.get_height(browser)
    height_exp.to_csv('%s/height_exp.csv' % (DIR))
    print('getting hca')
    #hca = kp.get_hca(browser)
    #hca.to_csv('%s/hca.csv' % (DIR))
    #print('getting pomeroy')
    #pomeroy = kp.get_pomeroy_ratings()
    #pomeroy.to_csv('%s/pomeroy.csv' % (DIR))
    print('complete')

def load(filename):
    return pandas.read_csv('%s/%s.csv' % (DIR, filename))

def is_slow_tempo(team):
    ff = load('four_factors')
    df = ff[ff['Team'] == team]
    if df.empty:
        return False
    else:
        return df.iloc[0].AdjTempo < 66

def is_fast_tempo(team):
    ff = load('four_factors')
    df = ff[ff['Team'] == team]
    if df.empty:
        return False
    else:
        return df.iloc[0].AdjTempo > 70

if __name__ == '__main__':
    run()