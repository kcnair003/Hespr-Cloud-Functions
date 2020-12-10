from __future__ import print_function
import json
import nltk
from nltk.corpus import stopwords
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
from profanity import profanity
import string
from google.cloud import firestore
import datetime
from googleapiclient.discovery import build
from googleapiclient import errors
from httplib2 import Http
from email.mime.text import MIMEText
import base64
from google.oauth2 import service_account
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from google.cloud import language_v1
import traceback

import sys
sys.path.append('/user_code/SentimentAnalysis.py')
from SentimentAnalysis import analyzeBlobSentiment, analyzeBlobSubjectivity, analyzeVADERSentiment

# Defines the SendGrid API key, which is used later in the algorithm
sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
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
    
def calculate_post_polarity(event, context):
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
    postID = resource_string_list[6]
    # Finds the name of the user
    post_ref = db.collection(u'posts').document(postID)
    # Defines the dictionary associated with the 'value' key
    value_dict = event['value']
    # Defines the dictionary associated the 'fields' key
    fields_dict = value_dict['fields']
    # Defines the dictionaries associated with the keys 'journal_text' and 'timestamp'
    post_text_dict = fields_dict['content']
    #timestamp_dict = fields_dict['timestamp']
    # Defines the journal text (string) and the timestamp (string)
    post_text = post_text_dict['stringValue']
    #timestamp_string = timestamp_dict['timestampValue']
    # Converts the timestamp into a 'datetime' object
    #timestamp_datetime = datetime.strptime(timestamp_string, '%Y-%m-%dT%H:%M:%SZ')
    # Checks for profanity and extracts keywords from the journal
    postPolarity = 0
    blobPolarity = 0
    blobSubjectivity = 0
    vaderPolarity = 0
    try:
        postPolarity = analyzeSentiment(post_text)
        blobPolarity = analyzeBlobSentiment(post_text)
        blobSubjectivity = analyzeBlobSubjectivity(post_text)
        vaderPolarity = analyzeVADERSentiment(post_text)
        data = { u'post_polarity_generated_timestamp': datetime.datetime.now(), 'post_polarity': postPolarity,  'TextBlob_Polarity': blobPolarity, 'TextBlob_Subjectivity': blobSubjectivity, 'VADER_Polarity': vaderPolarity}
        post_ref.update(data)
    except Exception as e:
        print("Sorry, something unexpected occurred. Please contact Hespr Support so that we can investigate the issue for you!")
        traceback.print_exc()
    try:
        user_post_dict = post_ref.get().to_dict()
        user_id = user_post_dict['uid']
        user_ref = db.collection(u'users').document(user_id)
        personal_post_ref = user_ref.collection('personal_posts').document(postID)
        data = { u'post_polarity_generated_timestamp': datetime.datetime.now(), 'post_polarity': postPolarity, 'TextBlob_Polarity': blobPolarity, 'TextBlob_Subjectivity': blobSubjectivity, 'VADER_Polarity': vaderPolarity, 'post_content': post_text}
        personal_post_ref.set(data)
    except Exception as e:
        print("Sorry, something unexpected occurred. Please contact Hespr Support so that we can investigate the issue for you!")
        traceback.print_exc()

