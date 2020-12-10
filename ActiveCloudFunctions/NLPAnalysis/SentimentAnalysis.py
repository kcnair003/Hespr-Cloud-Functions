from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer 
import nltk
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('brown')

def analyzeBlobSentiment(text):
    blob = TextBlob(str(text))
    return blob.sentiment.polarity

def analyzeBlobSubjectivity(text):
    blob = TextBlob(str(text))
    return blob.sentiment.subjectivity

def analyzeVADERSentiment(text):
    VADERanalyzer = SentimentIntensityAnalyzer()
    sentimentDict = VADERanalyzer.polarity_scores(text)
    return sentimentDict['compound']
"""
#The parameters that need to be passed are the text to be analyzed, a boolean to initialize TextBlob, and a boolean to initialize VADER
class SentimentAnalyzer:

    def __init__(self, TextBlobActivity, VADERActivity, **initialTexts):
        TextDict = {}
        for label, text in initialTexts.items():
            TextDict.update({label: text})
        self.TextBlobActivity = TextBlobActivity
        self.VADERActivity = VADERActivity
        self.TextBlobDict = {}
        self.VADERDict = {}
        if self.TextBlobActivity:
            for label, text in TextDict.items():
                self.TextBlobDict.update({label: self.calculateFormalSentiment(text)})
        if self.VADERActivity:
            self.VADERanalyzer = SentimentIntensityAnalyzer()
            for label, text in TextDict.items():
                self.VADERDict.update({label: self.VADERanalyzer.polarity_scores(text)})

    #Changes the text that the SentimentAnalyzer class references
    def addNewText(self, label, text):
        self.TextDict.update({label: text})
        if self.TextBlobActivity:
            self.TextBlobDict.update({label: self.calculateFormalSentiment(text)})
        

    #Creates a Textblob object to analyze polarity score and then returns the Textblob calculated sentiment related to its text
    def calculateFormalSentiment(text):
        blob = TextBlob(str(text))
        return blob.sentiment.polarity
"""
