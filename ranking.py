import pandas

from statistics import median
import math
import csv

EXPORT_ADJUSTED_DIFFS = True
MAX_DEPTH = 7
MIN_GAMES = 10
MAX_DIFF = 100
HOME_COURT_ADVANTAGE = 5
WIN_BONUS = 0

def update_ranking(year):
    score = pandas.read_csv('exports/%s/score.csv' % (year))
    weights = get_weights(score)
    print("Team weights complete")
    export_weights(weights, "exports/%s/weights.csv" % (year))
    score_detail = get_score_detail(score, weights)
    print("Scores detail complete")
    score_detail.to_csv("exports/%s/scores_detail.csv" % (year))
    print_ranking(get_ranking(weights), n=100, strategy='rank')

def gen_training_data(year, max_date):
    score = pandas.read_csv('exports/%s/score.csv' % (year))
    if max_date: #useful for separating data into training and test data
        score = score[pandas.to_datetime(score['date']) <= pandas.to_datetime(max_date)]
    weights = get_weights(score)
    print("Team weights complete")
    score_detail = get_score_detail(score, weights)
    score_detail.to_csv("exports/%s/scores_detail_training.csv" % (year))
    print_ranking(get_ranking(weights), n=100, strategy='rank')

def get_score_detail(score, weights):
    score_detail = transform_to_team_opponent(score)
    for i, row in score_detail.iterrows():
        opponent = row['opponent']
        score_detail.at[i, 'opponent_strength'] = weights.get(opponent, None)
    score_detail['diff'] = score_detail['team_score'] - score_detail['opponent_score']
    #score_detail['adjusted_diff'] = score_detail['diff'] + score_detail[
    #    'opponent_strength']
    score_detail['adjusted_diff'] = score_detail.apply(lambda row: get_adjusted_diff_for_row(row, weights), axis=1)
    #score_detail['adjusted_diff'] = score_detail.apply(lambda row: get_win_loss_grade_for_row(row, weights), axis=1)
    return score_detail

def transform_to_team_opponent(scores):
    team1_rows = scores[['date', 'team1', 'team1_score', 'team2', 'team2_score']].rename(columns={'date': 'date',
                                                                                                  'team1': 'team',
                                                                                                  'team1_score': 'team_score',
                                                                                                  'team2': 'opponent',
                                                                                                  'team2_score': 'opponent_score'})
    team1_rows['home_team'] = team1_rows['opponent']
    team2_rows = scores[['date', 'team2', 'team2_score', 'team1', 'team1_score']].rename(columns={'date': 'date',
                                                                                                  'team2': 'team',
                                                                                                  'team2_score': 'team_score',
                                                                                                  'team1': 'opponent',
                                                                                                  'team1_score': 'opponent_score'})
    team2_rows['home_team'] = team2_rows['team']
    return pandas.concat([team1_rows, team2_rows], ignore_index=True)

def get_weights(score):
    teams = get_teams(score, min_games=MIN_GAMES)
    scores = score.query('team1 in @teams and team2 in @teams')
    initial = dict((team, 0) for team in teams)
    weights = rank(initial, None, scores, MAX_DEPTH)
    return weights

def rank(weights, prev_weights, scores, depth):
    print('Ranking depth %s' % (depth))
    if is_stable(weights, prev_weights, strategy='weight', stability=0.99, tolerance=0.1) or depth == 0:
        return weights
    new_weights = dict(weights)
    for team in weights:
        new_weights[team] = get_weight(team, weights, scores.query('team1 == @team or team2 == @team'))
    #if depth > 1:
        #print('Iteration ' + str(MAX_DEPTH - depth + 1))
        #print_ranking(get_ranking(weights), n=10, strategy='rank')
    return rank(new_weights, weights, scores, depth-1)

def get_weight(team, weights, scores):
    adjusted_diffs = []
    for index, score in scores.iterrows():
        diff = get_adjusted_diff_for_weight(team, weights, score)
        #diff = get_weight_by_win_loss_grade(team, weights, score)
        adjusted_diffs.append(diff)
    return median(adjusted_diffs)

def get_adjusted_diff_for_row(row, weights):
    is_home = row.team == row.home_team
    try:
        opponent_strength = weights[row.opponent]
    except Exception:
        opponent_strength = 0
    return get_adjusted_diff(row.team_score, row.opponent_score, opponent_strength, is_home)

def get_adjusted_diff_for_weight(team, weights, score):
    #team is away, opponent is at home
    if team == score.team1:
        team_score = score.team1_score
        opponent_score = score.team2_score
        opponent_strength = weights[score.team2]
        is_home = False
    else:
        team_score = score.team2_score
        opponent_score = score.team1_score
        opponent_strength = weights[score.team1]
        is_home = True
    return get_adjusted_diff(team_score, opponent_score, opponent_strength, is_home)

def get_adjusted_diff(team_score, opponent_score, opponent_strength, is_home):
    if is_home == False:
        opponent_strength += HOME_COURT_ADVANTAGE
    win_bonus = WIN_BONUS if team_score > opponent_score else 0
    grade = team_score - opponent_score + opponent_strength + win_bonus
    return grade

def get_win_loss_grade_for_row(row, weights):
    return get_win_loss_grade(row['team1_score'], row['team2_score'], row['team2'], weights)

def get_weight_by_win_loss_grade(team, weights, score):
    #team is away, opponent is home
    if team == score.team1:
        team_score = score.team1_score
        opponent_score = score.team2_score
        opponent = score.team2
    #team is home, opponent is away
    else:
        team_score = score.team2_score
        opponent_score = score.team1_score
        opponent = score.team1
    return get_win_loss_grade(team_score, opponent_score, opponent, weights)

def get_win_loss_grade(team_score, opponent_score, opponent, weights):
    is_win = True if team_score > opponent_score else False
    try:
        opponent_strength = weights[opponent]
    except Exception:
        print('Can not find strength for opponent %s' % (opponent))
        opponent_strength = 0

    #wins
    if is_win and opponent_strength > 1:
        return 3
    elif is_win and opponent_strength > 0:
        return 2
    elif is_win and opponent_strength <= 0:
        return 1

    #losses
    if is_win == False and opponent_strength > 1:
        return -1
    elif is_win == False and opponent_strength > 0:
        return -2
    elif is_win == False and opponent_strength <= 0:
        return -3

def get_ranking(weights):
    return sorted(weights.items(), key=lambda x: x[1], reverse=True)

def print_ranking(ranking, n=64, strategy='seed'):
    for i in range(n):
        if strategy == 'seed':
            seed = str(math.ceil((i + 1) / 4))
            print(seed + '. ' + ranking[i][0] + ': ' + str(round(ranking[i][1], 1)))
        elif strategy == 'rank':
            print(str(i + 1) + '. ' + ranking[i][0] + ': ' + str(round(ranking[i][1], 1)))
        else:
            print(ranking[i])

def get_teams(scores, min_games=10):
    a = scores.groupby('team1').filter(lambda x: len(x) > min_games/2)
    b = scores.groupby('team2').filter(lambda x: len(x) > min_games/2)
    return pandas.concat([a.team1, b.team2]).unique()

def is_stable(weights, prev_weights, strategy='weight', stability=1.0, tolerance=1.0):
    if prev_weights == None:
        return False
    matches = 0
    if strategy == 'rank':
        ranking = sorted(weights, key=weights.get, reverse=True)
        ranking_prev = sorted(prev_weights, key=prev_weights.get, reverse=True)
        for team in weights:
            if abs(ranking.index(team) - ranking_prev.index(team)) <= tolerance:
                matches += 1
    elif strategy == 'weight':
        for team in weights:
            if abs(weights[team] - prev_weights[team]) <= tolerance:
                matches += 1

    match_rate = matches/len(weights)
    #print('Stability: ' + str(round(match_rate*100, 2)) + '%')
    return matches/len(weights) >= stability

def cap_diff(diff):
    if MAX_DIFF is None:
        return diff
    if diff > MAX_DIFF:
        return MAX_DIFF
    if diff < MAX_DIFF * -1:
        return MAX_DIFF * -1
    return diff

def bucket_diff(diff):
    if diff == 0: #for some reason there are ties
        return 0
    #wins
    if diff > 0 and diff < 5:
        return 1
    elif diff >= 5 and diff < 10:
        return 2
    elif diff >= 10 and diff < 15:
        return 3
    elif diff >= 15 and diff < 20:
        return 4
    elif diff >= 20:
        return 5
    #losses
    elif diff < 0 and diff > -5:
        return -1
    elif diff <= -5 and diff > -10:
        return -2
    elif diff <= -10 and diff > -15:
        return -3
    elif diff <= -15 and diff > -20:
        return -4
    elif diff <= -20:
        return -5
    else:
        print(diff)

def export_weights(weights, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Team', 'Score'])  # Header row
        for team in weights:
            writer.writerow([team, weights[team]])
    print(f"Exported adjusted diffs to {filename}.")
