import requests
import pandas
import json
import os
from datetime import datetime
import random

import analysis
import fuzzy
import kenpom

YEAR = 2025
BOOKS = ['fanduel', 'draftkings']
API_KEY = 'dfffbc8b6fa79f7f9394975fc1fb50f6'
FREE_API_KEY = 'd7eef29512374ba0023234d1b34b46f3'
URL = 'https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds?regions=us&oddsFormat=american&apiKey=%s' % (API_KEY)

TODAY = datetime.today().strftime('%Y-%m-%d')
HISTORICAL_DIR = 'exports/odds_historical'
DIR = 'exports/%s/%s/' % (YEAR, TODAY)
FILE_PATH = os.path.join(DIR, 'odds.json')
REPORT_FILE_PATH = os.path.join(DIR, 'report.csv')
SCORE_DETAIL = analysis.remove_d2_d3_games(pandas.read_csv('exports/%s/scores_detail.csv' % (YEAR)))
SCORE_SIMPLE = pandas.read_csv('exports/%s/score.csv' % (YEAR))
WEIGHTS = pandas.read_csv('exports/%s/weights.csv' % (YEAR))

TEST_START_DATE = pandas.Timestamp(f"{YEAR}-11-01")
TEST_END_DATE = pandas.Timestamp(f"{YEAR}-11-30")
TEST_DATES = pandas.date_range(start=TEST_START_DATE, end=TEST_END_DATE, freq="D")
TEST_BOOK = 'fanduel'
TEST_BET = 100
TRAINING_SCORES = analysis.remove_d2_d3_games(pandas.read_csv('exports/%s/scores_detail_training.csv' % (YEAR)))

def run():
    fetch_historical()
    #report()
    #display_report()

def fetch():
    print('Fetching odds...')
    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()
        os.makedirs(DIR, exist_ok=True)
        with open(FILE_PATH, 'w') as json_file:
            json.dump(data, json_file, indent=4)

def fetch_historical_by_date(date):
    historical_url = 'https://api.the-odds-api.com/v4/historical/sports/basketball_ncaab/odds?regions=us&oddsFormat=american&apiKey=%s&date=%sT12:00:00Z' % (API_KEY, date)
    print(historical_url)
    print('Fetching historical odds')
    response = requests.get(historical_url)
    data = response.json()
    os.makedirs(DIR, exist_ok=True)
    historical_file_path = os.path.join(HISTORICAL_DIR, ('odds-%s.json' % date))
    with open(historical_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def fetch_historical():
    print('fetching historical data')
    for date in TEST_DATES:
        fetch_historical_by_date(date.strftime('%Y-%m-%d'))

def validate_ev():
    print('Validating ev...')
    money_bet = 0
    money_won = 0
    random_money_won = 0 #random picks for control
    odds_won = []
    odds_lost = []
    for date in TEST_DATES:
        print(date)
        historical_file_path = os.path.join(HISTORICAL_DIR, ('odds-%s.json' % date.strftime('%Y-%m-%d')))
        with open(historical_file_path, 'r') as json_file:
            data = json.load(json_file)
        for game in data['data']:
            for bookmaker in game['bookmakers']:
                book = bookmaker['key']
                if book == TEST_BOOK:
                    for market in bookmaker['markets']:
                        if market['key'] == 'h2h':
                            result = analyze(game['away_team'], game['home_team'], book, market['outcomes'], TRAINING_SCORES)
                            if result:
                                pick = kenpom.predict_winner(result['team1'], result['team2'])
                                odds = result['team1_book_odds'] if pick == result['team1'] else result[
                                    'team2_book_odds']
                                if pick and odds > 0 and odds < 300:
                                    print('%s @ %s, pick = %s, odds = %s' % (result['team1'], result['team2'], pick, odds))
                                    actual_game = find_game(game['away_team'], game['home_team'], date)
                                    if actual_game != None:
                                        money_bet += TEST_BET
                                        random_pick = random.choice([result['team1'], result['team2']])
                                        random_pick_odds = result['team1_book_odds'] if random_pick == result['team1'] else result['team2_book_odds']
                                        actual_winner = actual_game['team1'] if actual_game['team1_score'] > actual_game['team2_score'] else actual_game['team2']
                                        is_correct = pick == actual_winner
                                        is_random_correct = random_pick == actual_winner
                                        if is_correct:
                                            payout = calculate_payout(TEST_BET, odds)
                                            money_won += payout
                                            odds_won.append(odds)
                                            #print('won')
                                            #print('Bet %s at %s and paid out %s' % (TEST_BET, odds, payout))
                                        else:
                                            odds_lost.append(odds)
                                            #print('lost')
                                        pct_gain = (money_won - money_bet) / money_bet * 100
                                        print('Pct gain: %s' % (pct_gain))

                                        if is_random_correct:
                                            random_payout = calculate_payout(TEST_BET, random_pick_odds)
                                            random_money_won += random_payout
                                    #else:
                                        #print('Skipping %s vs %s', result['team1'], result['team2'])

    #TODO: Check if there is a pattern in which odds tend to win and which tend to lose

    print('Bet %s and won %s' % (money_bet, money_won))
    print('Net: %s' % (money_won - money_bet))
    print('Pct gain: %s' % ((money_won - money_bet) / money_bet * 100))
    print('Random Pct gain: %s' % ((random_money_won - money_bet) / money_bet * 100))
    print(odds_won)
    print(odds_lost)

def find_game(odds_api_away_team, odds_api_home_team, date):
    away_team = fuzzy.map(odds_api_away_team)
    home_team = fuzzy.map(odds_api_home_team)
    date_str = date.strftime('%Y-%m-%d')
    games = SCORE_SIMPLE[SCORE_SIMPLE['date'] == date_str]
    match = games.query('team1 == @away_team and team2 == @home_team')
    try:
        return match.iloc[0].to_dict()
    except Exception:
        print('Unable to find matching game')
        return None

def calculate_payout(bet, odds):
    if odds > 0:
        return bet * (1 + (odds / 100))
    else:
        return bet * (1 + (100 / (odds * -1)))

def display_report():
    df = pandas.read_csv(REPORT_FILE_PATH)
    df_best_ev = df.loc[df.groupby(['team1', 'team2'])['highest_ev'].idxmax()]
    df_best_ev = df_best_ev.sort_values(by='highest_ev', ascending=False).reset_index(drop=True)
    print('------------------------------')
    print('TODAY\'S TOP 10')
    print('------------------------------')
    for index, row in df_best_ev.head(10).iterrows():
        fuzzy_match = '%s = %s, %s = %s' % (row['away_fuzzy_match'], row['team1'], row['home_fuzzy_match'], row['team2'])
        ev = format(row['highest_ev'])
        odds = row['team1_book_odds'] if row['team1_ev'] >= row['team2_ev'] else row['team2_book_odds']
        p = row['team1_p'] if row['team1_ev'] >= row['team2_ev'] else row['team2_p']
        team = row['team1'] if row['team1_ev'] >= row['team2_ev'] else row['team2']
        opponent = row['team1'] if team == row['team2'] else row['team2']
        is_home = team == row['team2']
        vs_or_at = 'vs' if is_home else '@'

        print('%s. %s %s %s' % (index + 1, team.upper(), vs_or_at, opponent))
        print(fuzzy_match)
        print('%s at %s' % (format_pct(p), format_odds(odds)))
        print('EV: %s' % (ev))
        print(row['book'])
        print('------------------------------')
        print('')
    print(df_best_ev.to_string(index=False))

def report():
    print('Generating report...')
    rows = []

    with open(FILE_PATH, 'r') as json_file:
        data = json.load(json_file)
    for game in data:
        for bookmaker in game['bookmakers']:
            book = bookmaker['key']
            if book in BOOKS:
                for market in bookmaker['markets']:
                    if market['key'] == 'h2h':
                        result = analyze(game['away_team'], game['home_team'], book, market['outcomes'], SCORE_DETAIL)
                        if result != None: #occurs if team name can't be matched
                            result['away_fuzzy_match'] = game['away_team']
                            result['home_fuzzy_match'] = game['home_team']
                            rows.append(result)
    df = pandas.DataFrame(rows)
    df = df.sort_values(by='highest_ev', ascending=False)
    df.to_csv(REPORT_FILE_PATH)
    print('Report complete')

def analyze(odds_api_away_team, odds_api_home_team, book, outcomes, scores):
    df = pandas.DataFrame(outcomes)
    outcome1 = df.iloc[0]
    outcome2 = df.iloc[1]

    away_team_odds = outcome1['price'] if outcome1['name'] == odds_api_away_team else outcome2['price']
    home_team_odds = outcome1['price'] if outcome1['name'] == odds_api_home_team else outcome2['price']

    away_team = fuzzy.map(odds_api_away_team)
    home_team = fuzzy.map(odds_api_home_team)

    if away_team == None:
        print('Unable to find team %s.  Skipping game.' % (odds_api_away_team))
        return None
    elif home_team == None:
        #print('Unable to find team %s.  Skipping game.' % (odds_api_home_team))
        return None
    #else:
        #print('Analyzing %s @ %s (%s odds)' % (away_team, home_team, book))

    result = analysis.analyze(book, scores, away_team, away_team_odds, home_team, home_team_odds, home_team, False)
    return result

def format(value):
    return "{:.2f}".format(value)

def format_pct(value):
    return f"{value:.1%}"

def format_odds(odds):
    if odds < 0:
        return odds
    else:
        return '+%s' % (odds)

if __name__ == '__main__':
    validate_ev()