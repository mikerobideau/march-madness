from bs4 import BeautifulSoup
import requests
import mysql.connector
import pandas
import os
from datetime import datetime
import time

class ncaa_dot_com_scraper():
    def __init__(self, year):
        self.year = year
        self.today = datetime.today().strftime('%Y-%m-%d')
        self.today_dir = 'exports/%s/%s/' % (self.year, self.today)
        self.year_dir = 'exports/%s/' % (self.year)
        self.rate_limit = 1

        self.score_filepath = os.path.join(self.year_dir, 'score.csv')
        self.teams_filepath = os.path.join(self.year_dir, 'teams.csv')
        self.todays_games_filepath = os.path.join(self.today_dir, 'todays_games.csv')

        self.connect()
        self.domain = 'https://www.ncaa.com'
        self.base = 'http://www.ncaa.com/scoreboard/basketball-men/d1'
        self.rankings_page  = 'https://www.ncaa.com/rankings/basketball-men/d1/ncaa-mens-basketball-net-rankings'
        self.bracket_page = 'https://www.ncaa.com/march-madness-live/bracket'
        self.schools_page = 'https://www.ncaa.com/schools-index'
        self.insert_count = 0
        self.inserts_per_commit = 100
        self.dates = self.get_dates()

    def scrape_schools(self):
        school_index_pages = 23
        for i in range(school_index_pages):
            page = i + 1
            current_schools_page = '%s/%s' % (self.schools_page, page)
            print('Scraping schools on %s' % (current_schools_page))
            r = requests.get(current_schools_page)
            soup = BeautifulSoup(r.content, 'html.parser')
            tbody = soup.find('tbody')
            rows = tbody.find_all('tr')
            i = 0
            for row in rows:
                links = row.find_all('a')
                link = links[1] #use second link because first link is a logo and has no text
                school_url = '%s%s' % (self.domain, link['href'])
                print(school_url)
                school = link.text
                nickname = self.get_nickname(school_url)
                if nickname:
                    values = [self.year, school, nickname]
                    print('%s %s' % (school, nickname))
                    self.insert_team(values)
                time.sleep(self.rate_limit)
            self.db.commit()
            print('Finished scraping schools')

    def get_nickname(self, url):
        try:
            r = requests.get(url)
            soup = BeautifulSoup(r.content, 'html.parser')
            schools_details = soup.find('dl', class_='school-details')
            dds = schools_details.find_all('dd')
            nickname = dds[1].text
            return nickname
        except Exception as e:
            return None

    def download_todays_games(self):
        r = requests.get(self.base)
        soup = BeautifulSoup(r.content, 'html.parser')
        games = []
        for game in soup.find_all('ul', {'class': 'gamePod-game-teams'}):
            teams = game.find_all('li')
            away_team = teams[0].select('.gamePod-game-team-name')[0].text
            home_team = teams[1].select('.gamePod-game-team-name')[0].text
            game = {'away_team': away_team, 'home_team': home_team}
            games.append(game)
        df = pandas.DataFrame(games)
        df.to_csv(self.todays_games_filepath)

    def scrape(self, scores=True, conferences=False, bracket=False, logos=False):
        print('Starting scraper')
        last_scraped_date = self.get_last_date_scraped(self.year)
        if scores:
            self.scrape_scores(last_scraped_date)
        if conferences:
            self.scrape_conferences()
        if bracket:
            self.scrape_bracket()
        if logos:
            self.scrape_logos()
        print('Finished scraping')

    def scrape_conferences(self):
        print('Scraping conferences')
        r = requests.get(self.rankings_page)
        soup = BeautifulSoup(r.content, 'html.parser')
        for row in soup.select_one('tbody').find_all('tr'):
            cells = row.find_all('td')
            team = cells[2].text
            conf_name = cells[3].text
            values = [self.year, team, conf_name]
            print(values)
            self.insert_conferences(values)
        self.db.commit()
        self.insert_count = 0
        print('Finished scraping conferences')

    def scrape_scores(self, last_scraped_date):
        today = pandas.to_datetime('today')
        for date in self.dates:
            if date <= today:
                date_str = date.strftime('%Y-%m-%d')
                if last_scraped_date == None or date > last_scraped_date:
                    print("Scraping games on %s " % (date_str))
                    date_url_str = date.strftime('%Y/%m/%d')
                    self.scrape_scores_by_date(date_url_str)
                else:
                    print('Already scraped %s' % (date_str))
        print('Committing remaining observations')
        self.db.commit()
        self.insert_count = 0
        print('Finished scraping scores')

    def scrape_scores_by_date(self, date):
        url = '%s/%s/all-conf' % (self.base, date)
        print(url)
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        for game in soup.find_all('ul', {'class': 'gamePod-game-teams'}):
            teams = game.find_all('li')
            team1 = teams[0].select('.gamePod-game-team-name')[0].text
            team1_score = teams[0].select('.gamePod-game-team-score')[0].text
            team2 = teams[1].select('.gamePod-game-team-name')[0].text
            team2_score = teams[1].select('.gamePod-game-team-score')[0].text
            if team1_score != '' and team2_score != '': #if game was played
                values = [self.year, date, team1, team1_score, team2, team2_score]
                print(values)
                self.insert_scores(values)

    def scrape_bracket(self):
        print('Scraping bracket')
        r = requests.get(self.bracket_page)
        soup = BeautifulSoup(r.content, 'html.parser')
        for team in soup.find_all('div', {'class', 'team'}):
            name = team.select('.body')[0].text
            if name != '':
                values = [self.year, name]
                print(values)
                self.insert_bracket(values)
        self.db.commit()
        self.insert_count = 0
        print('Finished scraping bracket')

    def scrape_logos(self):
        print('Scraping logos')
        teams = self.get_team_names()
        for team in teams:
            logo_url = self.get_logo(team)
            print(logo_url)
            values = [logo_url, self.year, team]
            self.update_logo(values)
        print('Finished scraping logos')

    def get_team_names(self):
        teams = []
        r = requests.get(self.rankings_page)
        soup = BeautifulSoup(r.content, 'html.parser')
        for row in soup.select_one('tbody').find_all('tr'):
            cells = row.find_all('td')
            teams.append(cells[2].text)
        return teams

    def get_logo(self, team):
        print(team)
        for date in self.dates:
            #print(date)
            url = '%s/%s/all-conf' % (self.base, date)
            #print(url)
            r = requests.get(url)
            soup = BeautifulSoup(r.content, 'html.parser')
            for game in soup.find_all('ul', {'class': 'gamePod-game-teams'}):
                teams = game.find_all('li')
                team1_name = teams[0].select('.gamePod-game-team-name')[0].text
                team2_name = teams[1].select('.gamePod-game-team-name')[0].text
                if team1_name == team:
                    return teams[0].select('.gamePod-game-team-logo-container')[0].select_one('img')['src']
                elif team2_name == team:
                    return teams[1].select('.gamePod-game-team-logo-container')[0].select_one('img')['src']

    def get_dates(self):
        start_date = pandas.Timestamp(f"{self.year-1}-11-01")
        end_date = pandas.Timestamp(f"{self.year}-03-31")
        return pandas.date_range(start=start_date, end=end_date, freq="D")

    def connect(self):
        self.db = mysql.connector.Connect(
                user="root",
                password ="password",
                host = "localhost",
                db ="march_madness",
                auth_plugin="mysql_native_password"
            )
        self.cursor = self.db.cursor()

    def insert_conferences(self, values):
        insert = '''
                INSERT INTO ncaa_d1_basketball_conference
                (year, team, conference)
                VALUES (%s,%s,%s)
                '''
        self.cursor.execute(insert, values)
        self.insert_count += 1
        if self.insert_count >= self.inserts_per_commit:
            print('Committing %s observations' % (self.inserts_per_commit))
            self.db.commit()
            self.insert_count = 0

    def insert_scores(self, values):
        insert = '''
                INSERT INTO ncaa_d1_basketball_score
                (year, date, team1, team1_score, team2, team2_score)
                VALUES (%s,%s,%s,%s,%s,%s)
                '''
        self.cursor.execute(insert, values)
        self.insert_count += 1
        if self.insert_count >= self.inserts_per_commit:
            print('Committing %s observations' % (self.inserts_per_commit))
            self.db.commit()
            self.insert_count = 0

    def insert_bracket(self, values):
        insert = '''
                INSERT INTO ncaa_d1_basketball_bracket
                (year, team)
                VALUES(%s, %s)
                '''
        result = self.cursor.execute(insert, values)
        return result

    def insert_team(self, values):
        insert = '''
            INSERT INTO ncaa_d1_basketball_team
            (year, school, nickname)
            VALUES(%s, %s, %s)
            '''
        result = self.cursor.execute(insert, values)
        return result

    def download_scores(self, year):
        query = '''
            SELECT
                year AS year,
                date,
                team1,
                team1_score,
                team2,
                team2_score
            FROM ncaa_d1_basketball_score
            WHERE year = 
        ''' + str(year)
        self.cursor.execute(query)
        df = pandas.DataFrame(self.cursor)
        df.to_csv(self.score_filepath, header=["year", "date", "team1", "team1_score", "team2", "team2_score"])

    def download_teams(self, year):
        query = '''
            SELECT
                year AS year,
                school,
                nickname
            FROM ncaa_d1_basketball_team
            WHERE year = 
        ''' + str(year)
        self.cursor.execute(query)
        df = pandas.DataFrame(self.cursor)
        df.to_csv(self.teams_filepath, header=["year", "team", "nickname"])

    def update_logo(self, values):
        insert = '''
                UPDATE ncaa_d1_basketball_conference
                SET logo = %s
                WHERE year = %s
                AND team = %s
                '''
        result = self.cursor.execute(insert, values)
        self.db.commit()
        return result

    def get_last_date_scraped(self, year):
        query = '''
                SELECT MAX(date) AS date
                FROM ncaa_d1_basketball_score
                WHERE year =
        ''' + str(year)
        self.cursor.execute(query)
        df = pandas.DataFrame(self.cursor)
        return pandas.to_datetime(df[0].iloc[0])