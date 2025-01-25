#Fuzzy matches names from the Odds API like "Kansas Jayhawks" with names from ncaa.com like "Kansas"

from fuzzywuzzy import fuzz
from metaphone import doublemetaphone
from jellyfish import jaro_winkler_similarity

MANDATORY_MATCH_WORDS = ['North', 'Northern', 'South', 'Southern', 'East', 'Eastern', 'West',
                         'Western', 'Tech']
MATCH_ANY_WORDS = ['Saint', 'St.', 'State', ]

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
    return scores

def score(str1, str2):
    token_ratio = fuzz.token_set_ratio(str1, str2)  #Handles reordering & partial matches
    jaro_score = jaro_winkler_similarity(str1.lower(), str2.lower()) * 100  #Boosts prefix similarity,
    # which is important here because it's more likely that the first part of the name (e.g., "Kansas") will match than
    # the second part (e.g., "Jayhawks")
    phonetic_score = 100 if phonetic_match(str1, str2) else 0  #100 if phonetic encoding matches
    return (token_ratio * 0.3) + (jaro_score * 0.5) + (phonetic_score * 0.3)

def phonetic_match(str1, str2):
    meta1 = doublemetaphone(str1.lower())
    meta2 = doublemetaphone(str2.lower())
    return any(m1 and m1 in meta2 for m1 in meta1)  # Check if any phonetic encodings match

def remove_last_word(name):
    """Improve fuzzy match by removing last word, which is always a mascot and not part of the school name"""
    words = name.split()
    return ' '.join(words[:-1])