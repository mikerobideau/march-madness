from bs4 import BeautifulSoup
import requests
import re
import mysql.connector

class ncaa_dot_com_scraper():
    def __init__(self, year, year_months):
        self.year = year
        self.year_months = year_months
        
        self.connect()
        self.base = 'http://www.ncaa.com/scoreboard/basketball-men/d1/'
        self.standings_page  = 'http://www.ncaa.com/standings/basketball-men/d1'
        self.insert_count = 0
        self.inserts_per_commit = 1000
        self.dates = self.get_dates()

    #---kickoff scraper---
    def scrape(self):
        print 'Starting scraper'
        #self.scrape_scores()
        self.scrape_standings()
        print 'Finished scraping'

    #---scrape scores
    def scrape_scores(self):
        print 'Scraping NCAA D1 Men\'s Basketball scores'
        for date in self.dates:
            print "Scraping games on %s " % (date)
            try:
                self.scrape_by_date(date)
            except:
                print "No games found"
        print 'Committing remaining observations'
        self.db.commit() #commit any remaining records
        self.insert_count = 0
        print 'Finished scraping scores'

    #---scrape a page by date---
    def scrape_by_date(self, date):
        soup = self.url_to_soup(self.base + date)
        linescores = soup.findAll('table', {'class': 'linescore'})

        for linescore in linescores:
            #Schools
            schoolLinks = linescore.findAll('a', href=re.compile('/schools/.*'))
            school1 = schoolLinks[0].text 
            school2= schoolLinks[1].text 
            #Scores
            
            finalscores = linescore.findAll('td', {'class': 'final score'})
            school1_score = finalscores[0].text
            school2_score = finalscores[1].text
            values = [self.year, school1, school1_score, school2, school2_score]
            self.insert_into_ncaa_d1_basketball_score(values)
    
    #---insert into scores
    def insert_into_ncaa_d1_basketball_score(self, values):
        insert = '''
                INSERT INTO ncaa_d1_basketball_score
                (year, team1, team1_score, team2, team2_score)
                VALUES (%s,%s,%s,%s,%s)
                '''
        self.cursor.execute(insert, values)
        self.insert_count += 1
        if self.insert_count >= self.inserts_per_commit:
            print 'Committing %s observations' % (self.inserts_per_commit)
            self.db.commit()
            self.insert_count = 0

    #---scrape standings
    def scrape_standings(self):
        print 'Scraping NCAA D1 Men\'s Basketball standings'
        soup = self.url_to_soup(self.standings_page)
        conference_divs = soup.findAll('div', class_=re.compile('ncaa-standings-conference-show.*'))
        
        for conference_div in conference_divs:
            conf_name = conference_div.find('div', {'class', 'ncaa-standings-conference-name'}).text
            #print '---'
            #print conf_name
            #print '---'
            #conference standings
            standings_table = conference_div.find('table', {'class': 'ncaa-standing-conference-table'})

            even_team_rows = standings_table.findAll('tr', {'class': 'even'})
            odd_team_rows = standings_table.findAll('tr', {'class': 'odd'})
            team_rows = even_team_rows + odd_team_rows
            for row in team_rows:
                tds = row.findAll('td')
                team = tds[0].text
                #print team
                conf_w = tds[1].text
                conf_l = tds[2].text
                conf_pct = tds[3].text
                w = tds[4].text
                l= tds[5].text
                pct = tds[6].text
                streak = tds[7].text
                rpi = tds[8].text
                vs_1_to_50 = tds[9].text
                vs_51_to_100 = tds[10].text
                vs_101_to_150 = tds[11].text
                vs_150_plus = tds[12].text
                values = [self.year, team, conf_name, conf_w, conf_l, conf_pct, w, l, pct, streak, rpi, vs_1_to_50, vs_51_to_100, vs_101_to_150, vs_150_plus]
                if team != "": #ignore header
                    self.insert_into_ncaa_d1_basketball_standing(values)
        self.db.commit() #insert remaining records
        self.insert_count = 0
        print 'Finished scraping standings'            

    #---insert standings
    def insert_into_ncaa_d1_basketball_standing(self, values):
        insert = '''
                INSERT INTO ncaa_d1_basketball_standing
                (year, team, conference, conf_w, conf_l, conf_pct, w, l, pct, streak, rpi, vs_1_to_50, vs_51_to_100, vs_101_to_150, vs_150_plus )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                '''
        self.cursor.execute(insert, values)
        self.insert_count += 1
        if self.insert_count >= self.inserts_per_commit:
            print 'Committing %s observations' % (self.inserts_per_commit)
            self.db.commit()
            self.insert_count = 0

    #---connect to database
    def connect(self):
        self.db = mysql.connector.Connect(
                user="root",
                password ="",
                host = "localhost",
                db ="march_madness"
            )
        self.cursor = self.db.cursor()

    #---get beautiful soup from a url---
    def url_to_soup(self, url):
        r = requests.get(url)
        data = r.text
        return BeautifulSoup(data)

    #---get dates
    def get_dates(self):
        #assigns 31 days to every month
        dates = list()
        days = [i + 1 for i in range(31)]
        for year_month in self.year_months:
            for day in days:
                if len(str(day)) == 1: #if date has one digit
                    day = '0%s' % (day) #add leading 0
                dates.append('%s%s' % (year_month, day))
        return dates

year = '2018' 
year_months = ['2017/11/', '2017/12/', '2018/01/', '2018/02/', '2018/03/']
scraper = ncaa_dot_com_scraper(year, year_months)
scraper.scrape()

