#Fuzzy matches names from the Odds API like "Kansas Jayhawks" with names from ncaa.com like "Kansas"
from fuzzywuzzy import fuzz
from metaphone import doublemetaphone
import os
import requests
import json
from datetime import datetime
import pandas

API_KEY = 'd7eef29512374ba0023234d1b34b46f3'
URL = 'https://api.the-odds-api.com/v4/sports/basketball_ncaab/participants?apiKey=%s' % (API_KEY)
YEAR = 2025
TODAY = datetime.today().strftime('%Y-%m-%d')
DIR = 'exports/%s/' % (YEAR)
ODDS_API_TEAMS_FILE_PATH = os.path.join(DIR, 'odds_api_teams.json')
ODDS_API_MAPPING_FILE_PATH = 'data/odds_api_mapping.csv'
MANDATORY_MATCH_WORDS = ['North', 'Northern', 'South', 'Southern', 'East', 'Eastern', 'West',
                         'Western', 'Tech']
MATCH_ANY_WORDS = ['Saint', 'St.', 'State', ]
WEIGHTS = pandas.read_csv('exports/%s/weights.csv' % (YEAR))

def main():
    #fetch()
    create_map()
    return

def map(name):
    try:
        df = pandas.read_csv(ODDS_API_MAPPING_FILE_PATH)
        match = df.loc[df["odds_api_name"] == name, "matched_name"]

        if not match.empty:
            return match.iloc[0]
        else:
            return None

    except FileNotFoundError:
        print(f"Error: {File} not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_num_rows_mapped():
    try:
        df = pandas.read_csv(ODDS_API_MAPPING_FILE_PATH)
        return len(df)
    except FileNotFoundError:
        print(f"Error: File not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def create_map():
    with open(ODDS_API_TEAMS_FILE_PATH, 'r') as json_file:
        data = json.load(json_file)
        print('%s of %s rows mapped' % (get_num_rows_mapped(), len(data)))
        for row in data:
            odds_api_name = row['full_name']
            existing_mapping = map(odds_api_name)
            if existing_mapping == None:
                print('Choose...')
                candidates = all_matches(odds_api_name, WEIGHTS['Team'])
                choice = choose_candidate(odds_api_name, candidates)
                if choice != None:
                    append_mapping_to_csv(odds_api_name, choice, ODDS_API_MAPPING_FILE_PATH)

def choose_candidate(name, candidates):
    print("%s:" % (name))

    for i, candidate in enumerate(candidates, 1):
        print(f"{i}. {candidate[0]}")

    print("0. Enter manually")
    print("-1. Skip")

    while True:
        try:
            choice = int(input("\nEnter number: "))
            if 1 <= choice <= len(candidates):
                return candidates[choice - 1][0]
            elif choice == 0:
                return input("\nEnter the correct name: ")
            elif choice == -1:
                return None
            else:
                print("Invalid choice. Please enter a number between 1 and", len(candidates))
        except ValueError:
            print("Invalid input. Please enter a number.")
    return choice[0]

def append_mapping_to_csv(name, matched_name, csv_file):
    file_exists = os.path.isfile(csv_file)
    df = pandas.DataFrame([[name, matched_name]], columns=["odds_api_name", "matched_name"])
    df.to_csv(csv_file, mode="a", header=not file_exists, index=False)
    print(f"Saved: {name} → {matched_name}\n")

def fetch():
    print('Fetching teams from odds api...')
    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()
        print(data)
        os.makedirs(DIR, exist_ok=True)
        with open(ODDS_API_TEAMS_FILE_PATH, 'w') as json_file:
            json.dump(data, json_file, indent=4)

def match(name, candidates):
    required_word = next((word for word in MANDATORY_MATCH_WORDS if word in name), None)
    require_any = next((word for word in MATCH_ANY_WORDS if word in name), None)
    matches = all_matches(name, candidates)
    if not matches:
        return None

    #if there is a required word like "Northern", make sure it is in the match
    valid_matches = [match for match in matches if required_word in match[0]] if required_word else matches

    #if there is a "require any" scenario like "St.", "State", or "Saint", make sure one is in the match
    if require_any:
        valid_matches = [match for match in valid_matches if any(word in match[0] for word in MATCH_ANY_WORDS)]

    best_match = valid_matches[0][0]
    score = valid_matches[0][1]
    #print('%s = %s (%s)' % (name, best_match, score))
    return {'name': best_match, 'score': score}

def all_matches(search_str, candidates):
    scores = [(candidate, score(search_str, candidate)) for candidate in candidates]
    scores.sort(key=lambda x: x[1], reverse=True)  #Sort by highest score
    return scores[:7]

def score(str1, str2):
    token_ratio = fuzz.token_set_ratio(str1, str2)  #Handles reordering & partial matches
    jaro_score = jaro_winkler_similarity(str1.lower(), str2.lower()) * 100  #Boosts prefix similarity,
    phonetic_score = 100 if phonetic_match(str1, str2) else 0  #100 if phonetic encoding matches
    #return (token_ratio * 0.7) + (phonetic_score * 0.3)
    return (token_ratio * 0.5) + (jaro_score * 0.2) + (phonetic_score * 0.3)

def phonetic_match(str1, str2):
    meta1 = doublemetaphone(str1.lower())
    meta2 = doublemetaphone(str2.lower())
    return any(m1 and m1 in meta2 for m1 in meta1)  # Check if any phonetic encodings match

def remove_last_word(name):
    #Improve fuzzy match by removing last word, which is always a mascot and not part of the school name
    words = name.split()
    return ' '.join(words[:-1])

if __name__ == '__main__':
    main()