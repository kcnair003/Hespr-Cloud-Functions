from rake_nltk import Rake
from rake_nltk import Metric
from nltk.corpus import stopwords

def rakeanalysis(journal):
    sw = stopwords.words("english")
    r = Rake(stopwords=sw, punctuations='?,.,(,),|,[,]', min_length=2, max_length=5)
    #Advanced Rake Algorithm - Specifies the stopwords, the punctuation that must be ignored, and the min/max length of the keywords
    r.extract_keywords_from_text(journal)
    results = r.get_ranked_phrases_with_scores()
    return results