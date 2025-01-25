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

def main():
    #fetch()
    report()

def fetch():
    print('Fetching odds...')
    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()
        os.makedirs(DIR, exist_ok=True)
        with open(FILE_PATH, 'w') as json_file:
            json.dump(data, json_file, indent=4)

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
                        result = process_outcomes(book, market['outcomes'])
                        rows.append(result)
    df = pandas.DataFrame(rows)
    df = df.sort_values(by='highest_ev', ascending=False)
    df.to_csv(REPORT_FILE_PATH)

def process_outcomes(book, outcomes):
    df = pandas.DataFrame(outcomes)
    outcome1 = df.iloc[0]
    outcome2 = df.iloc[1]
    team1_match = fuzzy.match(outcome1['name'], SCHOOLS)
    team2_match = fuzzy.match(outcome2['name'], SCHOOLS)
    team1 = team1_match['name']
    team2 = team2_match['name']
    result = analysis.analyze(book, SCORES, team1, outcome1['price'], team2, outcome2['price'], team1, False)
    return result

if __name__ == '__main__':
    main()