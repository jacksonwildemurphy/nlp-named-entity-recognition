# Written by Jackson Murphy.

training_file = open("train.txt")
sentence = []
line = training_file.readline()
while line:
    while line.strip():
        print("In the loop")
        sentence.append(line.split())
        line = training_file.readline()
    print("End of sentence:", sentence)
    sentence = []
