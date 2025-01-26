import requests
import pandas
import json
import os
from datetime import datetime
from fuzzywuzzy import process

import analysis

YEAR = 2025
BOOKS = ['fanduel', 'draftkings']
API_KEY = 'd7eef29512374ba0023234d1b34b46f3'
URL = 'https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds?regions=us&oddsFormat=american&apiKey=%s' % (API_KEY)

DIR = 'exports/%s/%s/' % (YEAR, TODAY)
FILE_PATH = os.path.join(DIR, 'odds.json')
REPORT_FILE_PATH = os.path.join(DIR, 'report.csv')
SCORES = analysis.remove_d2_d3_games(pandas.read_csv('exports/2025/scores_detail.csv'))
TEAMS = team_df = pandas.read_csv('exports/%s/teams.csv' % (YEAR))
WEIGHTS = pandas.read_csv('exports/%s/weights.csv' % (YEAR))

def main():
    fetch()
    #report()
    #display_report()
    print(fuzzy_match('North Carolina Tar Heels', TEAMS))

def fetch():
    print('Fetching odds...')
    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()
        os.makedirs(DIR, exist_ok=True)
        with open(FILE_PATH, 'w') as json_file:
            json.dump(data, json_file, indent=4)

def display_report():
    #
    # THIS REPORT NEEDS IMPROVEMENT
    # THERE ARE TOO MANY FUZZY MATCHING ERRORS WHEN TRYING TO MATCH TEAM NAMES FROM THE ODDS API
    #

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

def process_outcomes(odds_api_away_team, odds_api_home_team, book, outcomes):
    df = pandas.DataFrame(outcomes)
    outcome1 = df.iloc[0]
    outcome2 = df.iloc[1]

    away_team_odds = outcome1['price'] if outcome1['name'] == odds_api_away_team else outcome2['price']
    home_team_odds = outcome1['price'] if outcome1['name'] == odds_api_home_team else outcome2['price']

    away_team = fuzzy_match(odds_api_away_team, TEAMS)
    home_team = fuzzy_match(odds_api_home_team, TEAMS)

    result = analysis.analyze(book, SCORES, away_team, away_team_odds, home_team, home_team_odds, home_team, False)
    return result

def fuzzy_match(odds_api_name, teams):
    #convert from school name used in odds api to school name used on ncaa.com.  Need to use full name like "Kansas Jayhawks" becuase that's how odds api has it
    teams['team_and_nickname'] = teams['team'] + ' ' + teams['nickname']
    team_and_nicknames = teams['team_and_nickname'].tolist()
    match_and_score = process.extractOne(odds_api_name, team_and_nicknames)
    match = match_and_score[0]
    #but we're still not done, because for some infuriating reason the way ncaa.com writes the full team name on the school page isn't always the same as how they write the school part of the name on the score page (e.g. North Carolina A&T State Aggies -> N.C. A&T State)
    #so we need to fuzzy match just the school part to get the name in the score data
    school = teams.loc[teams["team_and_nickname"] == match].iloc[0]['team']
    score_page_teams = WEIGHTS['Team'].tolist()
    #score_page_match = fuzzy.match(match['name'], score_page_teams)
    match_and_score2 = process.extractOne(school, score_page_teams)
    match2 = match_and_score2[0]
    return match2

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