# Written by Jackson Murphy.

import re
import sys

# Returns a set of all the locations provided in the locations file
def _get_locations(locations_file_str):
    locations = set()
    locations_file = open(locations_file_str)
    for location in locations_file:
        locations.add(location)
    locations_file.close()
    return locations

# Returns a set of all the feature types provided in the command line arguments
def _get_features(argv):
    features = set()
    for i in range(4, len(argv)):
        features.add(argv[i])
    return features

# Returns a dictionary of all possible feature ids
def _create_feature_ids(training_file_str, features, locations):
    feature_ids = {}
    current_id = [0] # array instead of int to get pass-by-reference
    training_file = open(training_file_str)
    sentence = [] # initialize the first sentence
    line = training_file.readline()

    while line:
        # Build up a sentence like so: [[B-LOC,NNP,Israel], [O,NN,television], ...]
        if line.strip():
            sentence.append(line.split())
        else:
            if len(sentence) != 0: # Nec. bc there can be consecutive blank lines
                _add_sentence(sentence, feature_ids, current_id, features, locations)
                sentence.clear() # empty the list to accommodate next sentence
        line = training_file.readline()

    # Add feature entries for abbreviation, capitalization, and location
    _add_abbreviation(features, feature_ids, current_id)
    _add_capitalization(features, feature_ids, current_id)
    _add_location(features, locations, feature_ids, current_id)

    # Add entries for the special cases PHI, UNK, etc.
    _add_pseudos(feature_ids, current_id)
    training_file.close()
    return feature_ids

# Adds all possible features from the sentence to the feature_id dictionary
def _add_sentence(sentence, feature_ids, current_id, features, locations):
    for i in range(len(sentence)):
        _add_word(sentence, i, features, feature_ids, current_id)
        _add_word_context(sentence, i, features, feature_ids, current_id)
        _add_pos(sentence, i, features, feature_ids, current_id)
        _add_pos_context(sentence, i, features, feature_ids, current_id)

# Adds a word to the feature_id dictionary, if not already included
def _add_word(sentence, i, features, feature_ids, current_id):
    word = sentence[i][2]
    if ("word-" + word) not in feature_ids:
        feature_ids["word-" + word] = current_id[0]
        current_id[0] += 1

# Adds the words before and after sentence[i][2] to the feature id dictionary,
# as long as WORDCON was provided in the command line arguments
def _add_word_context(sentence, i, features, feature_ids, current_id):
    if "WORDCON" not in features:
        return

    add_prev_word = True
    add_next_word = True
    if i == 0 and len(sentence) > 1:
        # prev-word-PHI is added in _add_pseudos
        add_prev_word = False
    elif i == (len(sentence)-1) and len(sentence) > 1:
        # next-word-PHI is added in _add_pseudos
        add_next_word = False

    if add_prev_word:
        prev_word = sentence[i-1][2]
        if ("prev-word-" + prev_word) not in feature_ids:
            feature_ids["prev-word-" + prev_word] = current_id[0]
            current_id[0] += 1

    if add_next_word:
        next_word = sentence[i+1][2]
        if ("next-word-" + next_word) not in feature_ids:
            feature_ids["next-word-" + next_word] = current_id[0]
            current_id[0] += 1

# Adds a part of speech tag to the feature_id dictionary, if not already included
def _add_pos(sentence, i, features, feature_ids, current_id):
    if "POS" not in features:
        return
    pos = sentence[i][1]
    if ("pos-" + pos) not in feature_ids:
        feature_ids["pos-" + pos] = current_id[0]
        current_id[0] += 1

# Adds the pos tags before and after sentence[i][1] to the feature id dictionary,
# as long as POSCON was provided in the command line arguments
def _add_pos_context(sentence, i, features, feature_ids, current_id):
    if "POSCON" not in features:
        return

    add_prev_pos = True
    add_next_pos = True
    if i == 0 and len(sentence) > 1:
        # prev-pos-PHI is added in _add_pseudos
        add_prev_pos = False
    elif i == (len(sentence)-1) and len(sentence) > 1:
        # next-pos-PHI is added in _add_pseudos
        add_next_pos = False

    if add_prev_pos:
        prev_pos = sentence[i-1][1]
        if ("prev-pos-" + prev_pos) not in feature_ids:
            feature_ids["prev-pos-" + prev_pos] = current_id[0]
            current_id[0] += 1

    if add_next_pos:
        next_pos = sentence[i+1][1]
        if ("next-pos-" + next_pos) not in feature_ids:
            feature_ids["next-pos-" + next_pos] = current_id[0]
            current_id[0] += 1

# Adds a feature  to feature_ids indicating whether a word is abbreviated or not
def _add_abbreviation(features, feature_ids, current_id):
    if "ABBR" not in features:
        return
    feature_ids["abbreviated"] = current_id[0]
    current_id[0] += 1

# Adds a feature  to feature_ids indicating whether a word is capitalized or not
def _add_capitalization(features, feature_ids, current_id):
    if "CAP" not in features:
        return
    feature_ids["capitalized"] = current_id[0]
    current_id[0] += 1

# Adds each location provided in the location file to feature_ids
def _add_location(features, locations, feature_ids, current_id):
    if "LOCATION" not in features:
        return
    for location in locations:
        feature_ids["location-" + location] = current_id[0]; current_id[0] += 1

# Add entries into feature_ids dictionary for the special cases PHI, UNK, etc.
def _add_pseudos(feature_ids, current_id):
    feature_ids["word-UNK"] = current_id[0]; current_id[0] += 1

    if "WORDCON" in features:
        feature_ids["prev-word-UNK"] = current_id[0]; current_id[0] += 1
        feature_ids["next-word-UNK"] = current_id[0]; current_id[0] += 1
        feature_ids["prev-word-PHI"] = current_id[0]; current_id[0] += 1
        feature_ids["next-word-OMEGA"] = current_id[0]; current_id[0] += 1

    if "POS" in features:
        feature_ids["pos-UNKPOS"] = current_id[0]; current_id[0] += 1

    if "POSCON" in features:
        feature_ids["prev-pos-UNKPOS"] = current_id[0]; current_id[0] += 1
        feature_ids["next-pos-UNKPOS"] = current_id[0]; current_id[0] += 1
        feature_ids["prev-pos-PHIPOS"] = current_id[0]; current_id[0] += 1
        feature_ids["next-pos-OMEGAPOS"] = current_id[0]; current_id[0] += 1

def _generate_files_from_training_set(training_file_str, feature_ids, locations, features):
    # The two output files we are creating and will write to
    readable_file = open(training_file_str + ".readable", "w+")
    vector_file = open(training_file_str + ".vector", "w+")

    training_file = open(training_file_str)
    sentence = [] # initialize the first sentence
    line = training_file.readline()

    while line:
        # Build up a sentence like so: [[B-LOC,NNP,Israel], [O,NN,television], ...]
        if line.strip():
            sentence.append(line.split())
        else:
            if len(sentence) != 0: # Nec. bc there can be consecutive blank lines
                _write_sentence_to_readable(sentence, features, locations, readable_file)
                #_write_sentence_to_vector(sentence, features, locations, feature_ids, vector_file)
                sentence.clear() # empty the list to accommodate next sentence
        line = training_file.readline()

    training_file.close()
    readable_file.close()
    vector_file.close()



def _write_sentence_to_readable(sentence, features, locations, readable_file):
    # Write info to readable file for each word in the sentence
    for i in range(len(sentence)):
        readable_file.write("WORD: " +  sentence[i][2] +  "\n")
        readable_file.write("WORDCON: " +  _get_word_context(sentence,i, features, "train") + "\n")
        readable_file.write("POS: " + _get_pos(sentence, i, features, "train") + "\n")
        readable_file.write("POSCON: " + _get_pos_context(sentence, i, features, "train") + "\n")
        readable_file.write("ABBR: " + _get_abbreviation(sentence, i, features, "train") + "\n")
        readable_file.write("CAP: " + _get_capitalization(sentence, i, features, "train") + "\n")
        readable_file.write("LOCATION: " + _get_location(sentence, i, features, locations, "train") + "\n")
        readable_file.write("\r\n")

def _get_word_context(sentence, i, features, set_type):
    if "WORDCON" not in features:
        return "n/a"

    prev_word, next_word = "", ""
    got_prev_word, got_next_word = False, False

    if i == 0: # First word in the sentence
        prev_word = "PHI"
        got_prev_word = True
    elif i == (len(sentence)-1): # Last word in the sentence
        next_word = "OMEGA"
        got_next_word = True
    if not got_prev_word:
        prev_word = sentence[i-1][2]
    if not got_next_word:
        next_word = sentence[i+1][2]

    return prev_word + " " + next_word

def _get_pos(sentence, i, features, set_type):
    if "POS" not in features:
        return "n/a"
    else:
        return sentence[i][1]

def _get_pos_context(sentence, i, features, set_type):
    if "POSCON" not in features:
        return "n/a"
    prev_pos, next_pos = "", ""
    got_prev_pos, got_next_pos = False, False

    if i == 0: # First pos in the sentence
        prev_pos = "PHIPOS"
        got_prev_pos = True
    elif i == (len(sentence)-1): # Last pos in the sentence
        next_pos = "OMEGAPOS"
        got_next_pos = True
    if not got_prev_pos:
        prev_pos = sentence[i-1][1]
    if not got_next_pos:
        next_pos = sentence[i+1][1]

    return prev_pos + " " + next_pos

def _get_abbreviation(sentence, i, features, set_type):
    if "ABBR" not in features:
        return "n/a"
    word = sentence[i][2]
    # Abbreviations end with a period and consists entirely of alphabetic
    # characters and 1 or more periods, and are less than 5 characters
    pattern = re.compile("^(.*[a-zA-Z]+.*)*)$")
    if pattern.match(word) and len(word) < 5:
        return "yes"
    else:
        return "no"

def _get_capitalization(sentence, i, features, set_type):
    if "CAP" not in features:
        return "n/a"
    word = sentence[i][2]
    if word.istitle() or word.isupper():
        return "yes"
    else:
        return "no"

def _get_location(sentence, i, features, locations, set_type):
    if "LOCATION" not in features:
        return "n/a"
    word = sentence[i][2]
    if word in locations:
        return "yes"
    else:
        return "no"

##### START OF PROGRAM #####

if len(sys.argv) < 5 or len(sys.argv) > 11:
    print("You gave the wrong number of arguments.")
    print("Arguments should be: <train_file> <test_file> <locations_file> <feature types>")
    sys.exit(0)

locations = _get_locations(sys.argv[3])
features = _get_features(sys.argv)
feature_ids = _create_feature_ids(sys.argv[1], features, locations)

_generate_files_from_training_set(sys.argv[1], feature_ids, locations, features)

# for item in sorted(feature_ids.items(), key=lambda x: x[1], reverse=True):
#     print(item)
