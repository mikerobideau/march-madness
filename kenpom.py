from kenpompy.utils import login
import statsmodels.api as sm
import kenpompy.summary as kp
import pandas

YEAR = '2025'
USER = 'kingrobideau@gmail.com'
PASSWORD = 'Devdev77!'
DIR = 'exports/%s/kenpom' % (YEAR)

def run():
    #scrape()
    regression()

def prepare_date():
    #game scores
    df = pandas.read_csv('exports/%s/scores_detail.csv' % (YEAR))
    df = df[df['home_team'] == df['team']]
    df['win'] = df['diff'].apply(lambda x: 1 if x > 0 else 0)
    df['is_home'] = (df['team'] == df['home_team']).astype(int)
    print(df['is_home'])
    weights = pandas.read_csv('exports/%s/weights.csv' % (YEAR))
    weights = weights.rename(columns={'Score': 'Weight'})

    #merge team stats
    df = df.merge(weights, left_on='team', right_on='Team', how='inner')
    ff = load('four_factors')
    df = df.merge(ff, left_on='team', right_on='Team', how='inner')

    #merge opponent stats
    opp_weights = weights.add_prefix('opp_')
    df = df.merge(opp_weights, left_on='opponent', right_on='opp_Team', how='inner')
    opp_ff = ff.add_prefix('opp_')
    df = df.merge(opp_ff, left_on='opponent', right_on='opp_Team', how='inner')

    #interactions
    df['AdjOE_x_opp_AdjDE'] = df['AdjOE'] * df['opp_AdjDE']
    df['AdjDE_x_opp_AdjOE'] = df['AdjDE'] * df['opp_AdjOE']

    print(df.columns)
    return df

def regression():
    df = prepare_date()

    X = df[['AdjOE', 'AdjDE', 'opp_AdjOE', 'opp_AdjDE', 'is_home']]
    y = df['win']

    X = sm.add_constant(X)
    model = sm.Logit(y, X).fit()
    print(model.summary())

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

if __name__ == '__main__':
    run()