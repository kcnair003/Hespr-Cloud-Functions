from textblob import TextBlob, Word
from functools import reduce
import nltk
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('brown')
import random
import traceback

import sys
import string
sys.path.append('/user_code/TFIDF.py')
sys.path.append('/user_code/Ranker.py')
from TFIDF import tfidfanalysis
from Ranker import TextRank4Keyword as Ranker

def TextBlobNounTagging(journal):
    blob = TextBlob(journal)
    nouns = list()
    for noun_phrase in blob.noun_phrases:
        nouns.append(noun_phrase)
    for word, tag in blob.tags:
        #Checks if word is a noun
        if tag == 'NN' or tag == 'NP':
            #Checks if the word appears in the noun phrases
            if any(word.lemmatize() not in noun for noun in nouns):
                nouns.append(word.lemmatize())
        #Checks if the word is a verb
        if tag == 'VB':
            nouns.append(word.lemmatize())
    return nouns

def TextBlobRandomSampling(l, population):
    randomList = []
    try:
        for item in random.sample(l, population):
            randomList.append(str(item))
        return randomList
    except ValueError:
        if population > 0:
            print("The original number of words sampled was too high: " + str(population))
            print("The new number being sampled is: " + str(population-1))
            return TextBlobRandomSampling(l, population-1)
        else:
            return randomList
    except:
        traceback.print_exc()

def TextBlobKeywordGeneration(journal, keywords, iterations):
    nouns = TextBlobNounTagging(journal)
    finalList=[]
    textblobList = []
    textblobList = [TextBlobRandomSampling(nouns, keywords) for i in range(iterations)]
    prefinalList = keywordListMerge(*textblobList)
    finalList = [word.rstrip(string.punctuation) for word in prefinalList]
    return list(finalList)

def TextRankerKeywordGeneration(journal, keywords):
    textranker = Ranker()
    textranker.analyze(journal, candidate_pos = ['NOUN', 'PROPN'], window_size=4, lower=False)
    textrankerOutput = textranker.get_keywords(keywords)
    pretextrankerList = [x.lower() for x in textrankerOutput]
    textrankerList = [word.rstrip(string.punctuation) for word in pretextrankerList]
    return textrankerList

def TFIDFKeywordGeneration(journal):
    tfidfOutput = tfidfanalysis(journal)
    pretfidfList = [y.lower() for y in tfidfOutput]
    tfidfList = [word.rstrip(string.punctuation) for word in pretfidfList]
    return tfidfList

def keywordListMerge(*lists):
    setList = [set(l) for l in lists]
    print("Set of Lists:")
    print(setList)
    finalList= []
    intersectionList = list(reduce(lambda set1, set2: set1.intersection(set2), setList))
    print("Intersection of Lists")
    print(intersectionList)
    differenceList = list(reduce(lambda set1, set2: set1.symmetric_difference(set2), setList))
    print("Difference of Lists")
    print(differenceList)
    if len(intersectionList)!= 0:
        finalList.extend(item for item in intersectionList)
    if len(differenceList)!= 0:
        finalList.extend(item for item in differenceList)
    print("Final Merged List")
    print(finalList)
    return finalList

def KeywordGenerator(journal, TextRankerKeywords, TextblobKeywords, iterations):
    textblobList = TextBlobKeywordGeneration(journal, TextblobKeywords, iterations)
    print("Textblob List")
    print(textblobList)
    textrankerList = TextRankerKeywordGeneration(journal, TextRankerKeywords)
    print("TextRanker")
    print(textrankerList)
    tfidfList = TFIDFKeywordGeneration(journal)
    print("TFIDF")
    print(tfidfList)
    TextRanker_TextBlob_List = keywordListMerge(textrankerList, textblobList)
    print("RankerBlob")
    print(TextRanker_TextBlob_List)
    TextRanker_TFIDF_List = keywordListMerge(textrankerList, tfidfList)
    print("Ranker TFIDF")
    print(TextRanker_TFIDF_List)
    TextRanker_TFIDF_TextBlob_List = keywordListMerge(textrankerList, tfidfList, textblobList)
    print("Ranker TFIDF Blob")
    print(TextRanker_TFIDF_TextBlob_List)
    finalList = []
    for word in range(3):
        if TextRanker_TFIDF_TextBlob_List[word] not in finalList:
            finalList.append(TextRanker_TFIDF_TextBlob_List[word])
    for word in range(3):
        if TextRanker_TextBlob_List[word] not in finalList:
            finalList.append(TextRanker_TextBlob_List[word])
    for word in range(3):
        if TextRanker_TFIDF_List[word] not in finalList:
            finalList.append(TextRanker_TFIDF_List[word])
    for word in TextRanker_TFIDF_TextBlob_List:
        if word not in finalList:
            finalList.append(word)
    for word in TextRanker_TFIDF_List:
        if word not in finalList:
            finalList.append(word)
    for word in TextRanker_TextBlob_List:
        if word not in finalList:
            finalList.append(word)
    print(finalList)
    return finalList

def finalKeywords(journal, TextRankerKeywords, TextblobKeywords, iterations):
    try:
        return KeywordGenerator(journal, TextRankerKeywords, TextblobKeywords, iterations)
    except:
        traceback.print_exc()



