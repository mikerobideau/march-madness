import requests
import pandas
import json
import os
from datetime import datetime

import analysis
import fuzzy

YEAR = 2025
BOOKS = ['fanduel', 'draftkings']
API_KEY = 'd7eef29512374ba0023234d1b34b46f3'
URL = 'https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds?regions=us&oddsFormat=american&apiKey=%s' % (API_KEY)
TODAY = datetime.today().strftime('%Y-%m-%d')
DIR = 'exports/%s/%s/' % (YEAR, TODAY)
FILE_PATH = os.path.join(DIR, 'odds.json')
REPORT_FILE_PATH = os.path.join(DIR, 'report.csv')
SCHOOLS = pandas.read_csv('exports/%s/weights.csv' % (YEAR))['Team'].to_list()
SCORES = analysis.remove_d2_d3_games(pandas.read_csv('exports/2025/scores_detail.csv'))
TODAYS_GAMES_FILEPATH = os.path.join(DIR, 'todays_games.csv')
TODAYS_GAMES = pandas.read_csv(TODAYS_GAMES_FILEPATH)

def main():
    #fetch()
    report()
    display_report()

def fetch():
    print('Fetching odds...')
    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()
        os.makedirs(DIR, exist_ok=True)
        with open(FILE_PATH, 'w') as json_file:
            json.dump(data, json_file, indent=4)

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
                        result = process_outcomes(game['away_team'], game['home_team'], book, market['outcomes'])
                        result['away_fuzzy_match'] = game['away_team']
                        result['home_fuzzy_match'] = game['home_team']
                        if result != None: #occurs if team name can't be matched
                            rows.append(result)
    df = pandas.DataFrame(rows)
    df = df.sort_values(by='highest_ev', ascending=False)
    df.to_csv(REPORT_FILE_PATH)
    print('Report complete')

def process_outcomes(away, home, book, outcomes):
    df = pandas.DataFrame(outcomes)
    outcome1 = df.iloc[0]
    outcome2 = df.iloc[1]
    away_team_match = fuzzy.match(away, SCHOOLS)
    home_team_match = fuzzy.match(home, SCHOOLS)
    away_team = away_team_match['name']
    home_team = home_team_match['name']
    away_team_odds = outcome1['price'] if outcome1['name'] == away else outcome2['price']
    home_team_odds = outcome1['price'] if outcome1['name'] == home else outcome2['price']
    result = analysis.analyze(book, SCORES, away_team, away_team_odds, home_team, home_team_odds, home_team, False)
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
    main()