import nltk
nltk.download('punkt')
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

def tfidfanalysis(journal):
  tfidf = TfidfVectorizer(stop_words='english', use_idf=True)
  intermediate = tfidf.fit_transform(journal.split(" "))
  final_tfidf = tfidf.transform([journal])
  df = pd.DataFrame(final_tfidf.T.todense(), index=tfidf.get_feature_names(), columns=["tfidf"])
  df.sort_values(by=["tfidf"],inplace=True, ascending=False)
  final = df.head(10)
  keywordList = []
  for row in final.iterrows():
    keywordList.append(row[0])
  return keywordList