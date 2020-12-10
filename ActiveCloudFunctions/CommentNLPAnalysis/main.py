from __future__ import print_function
import json
import string
from google.cloud import firestore
import datetime
from googleapiclient.discovery import build
from googleapiclient import errors
from httplib2 import Http
import base64
from google.oauth2 import service_account
from google.cloud import language_v1
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
    
def calculate_comment_polarity(event, context):
    """Triggered by a change to a Firestore document.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    resource_string = context.resource
    resource_string_list = resource_string.split('/')
    post_id = resource_string_list[6]
    comment_id = resource_string_list[8]
    post_ref = db.collection(u'posts').document(post_id)
    comments_ref = post_ref.collection(u'comments').document(comment_id)
    # Defines the dictionary associated with the 'value' key
    value_dict = event['value']
    # Defines the dictionary associated the 'fields' key
    fields_dict = value_dict['fields']
    # Defines the dictionaries associated with the key 'comment'
    comment_text_dict = fields_dict['comment']
    # Defines the journal text (string) and the timestamp (string)
    comment_text = comment_text_dict['stringValue']
    comment_polarity = 0
    blobPolarity = 0
    blobSubjectivity = 0
    vaderPolarity = 0
    try:
        comment_polarity = analyzeSentiment(comment_text)
        blobPolarity = analyzeBlobSentiment(comment_text)
        blobSubjectivity = analyzeBlobSubjectivity(comment_text)
        vaderPolarity = analyzeVADERSentiment(comment_text)
        data = { u'comment_polarity_generated_timestamp': datetime.datetime.now(), u'comment_polarity': comment_polarity, 'TextBlob_Polarity': blobPolarity, 'TextBlob_Subjectivity': blobSubjectivity, 'VADER_Polarity': vaderPolarity}
        comments_ref.set(data, merge=True)
    except Exception as e:
        print("Sorry, something unexpected occurred. Please contact Hespr Support so that we can investigate the issue for you!")
        traceback.print_exc()
    try:
        user_comment_dict = comments_ref.get().to_dict()
        user_id = user_comment_dict['uid']
        user_ref = db.collection(u'users').document(user_id)
        personal_comment_ref = user_ref.collection('personal_comments').document(comment_id)
        data = { u'comment_polarity_generated_timestamp': datetime.datetime.now(), 'comment_polarity': comment_polarity, 'TextBlob_Polarity': blobPolarity, 'TextBlob_Subjectivity': blobSubjectivity, 'VADER_Polarity': vaderPolarity, 'comment_content': comment_text, 'post_id': post_id}
        personal_comment_ref.set(data)
    except Exception as e:
        print("Sorry, something unexpected occurred. Please contact Hespr Support so that we can investigate the issue for you!")
        traceback.print_exc()