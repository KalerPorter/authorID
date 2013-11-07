import collections
import glob
import os
import math
import re

#the # of most popular words of each author is intersected together. this intersection is removed from everybody
MAX_TO_REMOVE = 200

#minimum number of times a word has to be repeated before it's considered
OCCURENCE_LIMIT = 3

M = 10

#the first half of each book is used to train
#the last half is divided this number of times and fed individually for classification
SECTIONS = 10

REMOVE = re.compile('[^A-Za-z ]')

def Strip(s):
    return REMOVE.sub('', s)


class BayeClass:
    def __init__(self):
        self.authors = {}

    def Train(self, words, author):
        if self.authors.get(author, None) is None:
            self.authors[author] = collections.defaultdict(int)
        for word in words:
            self.authors[author][word.lower()] += 1

    def Print(self):
        for author, data in self.authors.items():
            print author
            print sorted(data.items(), key=lambda x: x[1], reverse=True)[:50]

    def Prepare(self):
        mostCommon = None
        for author, data in self.authors.items():
            if mostCommon is None:
                mostCommon = \
                    set(x[0] for x in sorted(data.items(), reverse=True, key=lambda x: x[1])[:MAX_TO_REMOVE])
            mostCommon = mostCommon.intersection(
                set(x[0] for x in sorted(data.items(), reverse=True, key=lambda x: x[1])[:MAX_TO_REMOVE]))

        for author, data in self.authors.items():
            self.authors[author] = \
                dict((item for item in data.items() if item[1] > OCCURENCE_LIMIT and item[0] not in mostCommon))

    def Classify(self, words):
    #vocabulary
    #docs_j     the subset of documents from Examples for which the target value is
    #P(v_j)     |docs_j| / |Examples|
    #Text_j     a single document created by concatenating all members of docs_j
    #n          total numbers of distinct word poitions in Test_j
    #foreach word w_k in Vocabulary
    #n_k        number of times w_k occurs in Text_j
    #P(w_k|v_j) (n_k+1)/(n+|Vocabulary|)

        bestValue = 0
        best = 0

        for author, data in self.authors.items():
            n = sum(data.values())
            P_vj = math.log1p(1 / float(len(self.authors.keys())))

            for word in words:
                P_vj += math.log1p(float(data.get(word, 0) + 1) / float(n))

            if P_vj > bestValue:
                bestValue = P_vj
                best = author
        return best


def main():
    worst_book = 1
    correct_predictions = 0
    wrong_predictions = 0

    os.chdir("books")
    fileNames = [files for files in glob.glob("*.txt")]
    print "reading",
    for name in fileNames:
        print name,
    print

    bay = BayeClass()

    #TRAIN BASED ON THE FIRST HALF OF EACH BOOK
    for name in fileNames:
        with open(name, "r") as file:
            author = file.readline().strip()
            words = [word.lower() for line in file for word in Strip(line).split()]
            toTrain = len(words) / 2
            bay.Train(words[:toTrain], author)

    bay.Prepare()

    #CLASSIFY BASED ON THE LAST HALF (divided up SECTIONS number of times)
    for name in fileNames:
        with open(name, "r") as file:
            author = file.readline().strip()
            words = [word.lower() for line in file for word in Strip(line).split()]

            toTrain = len(words) / 2
            sectionLength = (len(words) - toTrain) / SECTIONS

            correct_book = 0
            wrong_book = 0
            for i in range(SECTIONS):
                if toTrain + sectionLength * (i + 1) > len(words):
                    classifyMe = words[toTrain + sectionLength * i:]
                else:
                    classifyMe = words[toTrain + sectionLength * i:toTrain + sectionLength * (i + 1)]

                predictedAuthor = bay.Classify(classifyMe)
                print name, "by", predictedAuthor, \
                    "\t( words", toTrain + sectionLength * i, "to", toTrain + sectionLength * (i + 1), ")"

                if predictedAuthor == author:
                    correct_predictions += 1
                    correct_book += 1
                else:
                    wrong_predictions += 1
                    wrong_book += 1

            if correct_book / float(correct_book + wrong_book) < worst_book:
                worst_book = correct_book / float(correct_book + wrong_book)

    print "Success rate:", "{0:.0f}%" \
        .format(correct_predictions / float(correct_predictions + wrong_predictions) * 100),
    print "\tWorst book: {0:.0f}%".format(worst_book * 100)


if __name__ == "__main__":
    # cProfile.run('main()')
    main()