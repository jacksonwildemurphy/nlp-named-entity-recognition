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
    _add_location(features, feature_ids, current_id)

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
    feature_ids["abbreviated"] = current_id[0]; current_id[0] += 1

# Adds a feature to feature_ids indicating whether a word is capitalized or not
def _add_capitalization(features, feature_ids, current_id):
    if "CAP" not in features:
        return
    feature_ids["capitalized"] = current_id[0]; current_id[0] += 1

# Adds a feature to feature_ids indicating whether a word is a location or not
def _add_location(features, feature_ids, current_id):
    if "LOCATION" not in features:
        return
    feature_ids["is-location"] = current_id[0]; current_id[0] += 1

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
        if line.strip(): # line is not empty
            sentence.append(line.split())
        else:
            if len(sentence) != 0: # Nec. bc there can be consecutive blank lines
                _write_sentence_to_readable(sentence, features, locations, readable_file)
                _write_sentence_to_vector(sentence, features, locations, feature_ids, vector_file)
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
    pattern = re.compile("^(.*[a-zA-Z]+.*)*$")
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

# Writes each word in the sentence to a vector output file
def _write_sentence_to_vector(sentence, features, locations, feature_ids, vector_file):
    ids = []
    label = None # initialize integer representation of the word's label
    # Write info to vector file for each word in the sentence
    for i in range(len(sentence)):
        label = _label2int(sentence[i][0])
        vector_file.write(str(_label2int(sentence[i][0])) + " ")
        ids.append(_get_word_id(sentence,i, feature_ids))
        ids += _get_word_context_ids(sentence,i, features, feature_ids)
        ids.append(_get_pos_id(sentence, i, features, feature_ids))
        ids += _get_pos_context_ids(sentence, i, features, feature_ids)
        ids.append(_get_abbreviation_id(sentence, i, features, feature_ids))
        ids.append(_get_capitalization_id(sentence, i, features, feature_ids))
        ids.append(_get_location_id(sentence, i, features, feature_ids, locations))
        _print_vector(label, ids)
        ids.clear()

# Returns an integer corresponding to the given BIO label
def _label2int(label):
    if label == "O":
        return 0
    elif label == "B-PER":
        return 1
    elif label == "I-PER":
        return 2
    elif label == "B-LOC":
        return 3
    elif label == "I-LOC":
        return 4
    elif label == "B-ORG":
        return 5
    elif label == "I-ORG":
        return 6
    else:
        raise Exception("Received a bad BIO label!")

# Returns the id for the word sentence[i][2], or the id for "word-UNK"
# if the word doesn't have an associated id
def _get_word_id(sentence,i, feature_ids):
    word = sentence[i][2]
    if ("word-" + word) in feature_ids:
        word_id = feature_ids[("word-" + word)]
    else:
        word_id = feature_ids["word-UNK"]
    return word_id

# Returns the two id numbers associated with the words before and after the word
# sentence[i][3]. If word context is not in the features set, returns None
# If ids are not found for the previous and/or next words, returns "prev-word-UNK"
# and "next-word-UNK" respectively
def _get_word_context_ids(sentence,i, features, feature_ids):
    if "WORDCON" not in features:
        return None
    prev_word_id = None
    if i == 0:
        prev_word_id = feature_ids["prev-word-PHI"]
    else:
        prev_word = sentence[i-1][2]
        if ("prev-word-" + prev_word) in feature_ids:
            prev_word_id = feature_ids[("prev-word-" + prev_word)]
        else:
            prev_word_id = feature_ids["prev-word-UNK"]

    # Now get the id for the following word
    next_word_id = None
    if i == len(sentence)-1:
        next_word_id = feature_ids["next-word-OMEGA"]
    else:
        next_word = sentence[i+1][2]
        if ("next-word-" + next_word) in feature_ids:
            next_word_id = feature_ids[("next-word-" + next_word)]
        else:
            next_word_id = feature_ids["next-word-UNK"]

    return [prev_word_id, next_word_id]

# Returns the id number associated with the POS tag for
# sentence[i][3]. But if POS is not in the features set, returns None
def _get_pos_id(sentence, i, features, feature_ids):
    if "POS" not in features:
        return None
    pos = sentence[i][1]
    pos_id = None
    if ("pos-" + pos) in feature_ids:
        pos_id = feature_ids[("pos-" + pos)]
    else:
        pos_id = feature_ids["UNKPOS"]
    return pos_id

# Returns the two id numbers associated with the pos tags before and after the pos tag
# sentence[i][1]. If pos context is not in the features set, returns None
# If ids are not found for the previous and/or next pos, returns "prev-pos-UNKPOS"
# and "next-pos-UNKPOS" respectively
def _get_pos_context_ids(sentence, i, features, feature_ids):
    if "POSCON" not in features:
        return None
    prev_pos_id = None
    if i == 0:
        prev_pos_id = feature_ids["prev-pos-PHIPOS"]
    else:
        prev_pos = sentence[i-1][1]
        if ("prev-pos-" + prev_pos) in feature_ids:
            prev_pos_id = feature_ids[("prev-pos-" + prev_pos)]
        else:
            prev_pos_id = feature_ids["prev-pos-UNK"]

    next_pos_id = None
    if i == len(sentence)-1:
        next_pos_id = feature_ids["next-pos-OMEGAPOS"]
    else:
        next_pos = sentence[i+1][1]
        if ("next-pos-" + next_pos) in feature_ids:
            next_pos_id = feature_ids[("next-pos-" + next_pos)]
        else:
            next_pos_id = feature_ids["next-pos-UNK"]

    return [prev_pos_id, next_pos_id]

# Returns the id number of the abbreviation feature
# But if ABBR is not in the features set, returns None
def _get_abbreviation_id(sentence, i, features, feature_ids):
    if "ABBR" not in features:
        return None
    if _get_abbreviation(sentence, i, features, "train") == "yes":
        return feature_ids["abbreviated"]
    else:
        return None

# Returns the id number of the capitalization feature
# But if CAP is not in the features set, returns None
def _get_capitalization_id(sentence, i, features, feature_ids):
    if "CAP" not in features:
        return None
    if _get_capitalization(sentence, i, features, "train") == "yes":
        return feature_ids["capitalized"]
    else:
        return None

# Returns the id number of the location feature
# But if LOCATION is not in the features set, returns None
def _get_location_id(sentence, i, features, feature_ids, locations):
    if "LOCATION" not in features:
        return None
    if _get_location(sentence, i, features, locations, "train") == "yes":
        return feature_ids["is-location"]
    else:
        return None

# Sorts in ascending order an array of feature ideas for a word, and then prints
# on a single line like so: <label> <feature_id1>:1  <feature_id2>:1 ...
def _print_vector(label, ids):
    print(str(label), end=" ")

    # Populate a new array with ids but no None elements from the id array
    condensed_ids = []
    for id in ids:
        if id != None:
            condensed_ids.append(id)

    condensed_ids.sort()
    for id in condensed_ids:
        print(str(id), end=":1 ")
    print("") #  Next word on a new line

##### START OF PROGRAM #####

if len(sys.argv) < 5 or len(sys.argv) > 11:
    print("You gave the wrong number of arguments.")
    print("Arguments should be: <train_file> <test_file> <locations_file> <feature types>")
    sys.exit(0)

locations = _get_locations(sys.argv[3])
features = _get_features(sys.argv)
feature_ids = _create_feature_ids(sys.argv[1], features, locations)

for item in sorted(feature_ids.items(), key=lambda x: x[1], reverse=True):
    print(item)

_generate_files_from_training_set(sys.argv[1], feature_ids, locations, features)
