from __future__ import print_function
import json
import nltk
from nltk.corpus import stopwords
import pandas as pd
import spacy
import string
from google.cloud import firestore
import datetime
from httplib2 import Http
from email.mime.text import MIMEText
import base64
from google.oauth2 import service_account
import os
from google.cloud import language_v1
from googleapiclient.discovery import build
from googleapiclient import errors
import traceback

import sys
sys.path.append('/user_code/SentimentAnalysis.py')
from SentimentAnalysis import analyzeBlobSentiment, analyzeBlobSubjectivity, analyzeVADERSentiment

# Establishes the Firestore client
db = firestore.Client()

def analyzeSentiment(text_phrase):
    # Defines the client, type of document, and the language used in the sentiment analysis
    client = language_v1.LanguageServiceClient()
    language = "en"
    document = language_v1.Document(content=text_phrase, type_=language_v1.Document.Type.PLAIN_TEXT, language=language)
    response = client.analyze_sentiment(request={'document': document})
    # Uses the analyze_sentiment() method to find the overall polarity and magnitude of the text
    textPolarity = response.document_sentiment.score
    return(textPolarity)
    
def calculate_polarity(event, context):
    """Triggered by a change to a Firestore document.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    resource_string = context.resource
    # print out the resource string that triggered the function
    #print(f"Function triggered by change to: {resource_string}.")
    # now print out the entire event object
    #print(str(event))
    # Finds the user ID associated with the journal entry
    resource_string_list = resource_string.split('/')
    user_id = resource_string_list[6]
    journal_id = resource_string_list[8]
    # Finds the name of the user
    name_ref = db.collection(u'users').document(user_id)
    name_doc = name_ref.get()
    name_dict = name_doc.to_dict()
    user_name = name_dict['nickname']
    # Defines the dictionary associated with the 'value' key
    value_dict = event['value']
    # Defines the dictionary associated the 'fields' key
    fields_dict = value_dict['fields']
    # Defines the dictionaries associated with the keys 'journal_text' and 'timestamp'
    journal_text_dict = fields_dict['journal_text']
    #timestamp_dict = fields_dict['timestamp']
    # Defines the journal text (string) and the timestamp (string)
    journal_text = journal_text_dict['stringValue']
    #timestamp_string = timestamp_dict['timestampValue']
    # Converts the timestamp into a 'datetime' object
    #timestamp_datetime = datetime.strptime(timestamp_string, '%Y-%m-%dT%H:%M:%SZ')
    # Checks for profanity and extracts keywords from the journal
    try:
        journalPolarity = analyzeSentiment(journal_text)
        blobPolarity = analyzeBlobSentiment(journal_text)
        blobSubjectivity = analyzeBlobSubjectivity(journal_text)
        vaderPolarity = analyzeVADERSentiment(journal_text)
        user_ref = db.collection(u'guided_journals').document(user_id)
        keyword_doc_ref = user_ref.collection(u'daily_journals').document(journal_id)
        data = { u'journal_polarity_generated_timestamp': datetime.datetime.now(), 'journal_polarity': journalPolarity, 'TextBlob_Polarity': blobPolarity, 'TextBlob_Subjectivity': blobSubjectivity, 'VADER_Polarity': vaderPolarity}
        keyword_doc_ref.update(data)
    except Exception as e:
        print("Sorry, something unexpected occurred. Please contact Hespr Support so that we can investigate the issue for you!")
        traceback.print_exc()