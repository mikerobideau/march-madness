from scraper import ncaa_dot_com_scraper
import ranking
import daily_report

YEAR = 2023

def main():
    #scraper = ncaa_dot_com_scraper(YEAR)
    #scraper.scrape()
    #scraper.download_scores(YEAR)

    ranking.update_ranking(YEAR)
    ranking.gen_training_data(YEAR, ('%s-12-31' % (YEAR - 1)))

    #daily_report.run()

if __name__ == '__main__':
    main()