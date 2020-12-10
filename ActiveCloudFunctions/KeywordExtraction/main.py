from __future__ import print_function
from google.cloud import firestore
from httplib2 import Http
from email.mime.text import MIMEText
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import os
import traceback
import string
import datetime

import sys
sys.path.append('/user_code/KeywordAlgorithm.py')
sys.path.append('/user_code/DataProtection.py')
sys.path.append('/user_code/ProfanityFilter.py')
from KeywordAlgorithm import finalKeywords
from DataProtection import encrypt, decrypt
from ProfanityFilter import detect_profanity


# Defines the SendGrid API key, which is used later in the algorithm
sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
# Establishes the Firestore client
db = firestore.Client()

@firestore.transactional
def update_frequency_in_transaction(transaction, doc_ref):
    snapshot = doc_ref.get(transaction=transaction)
    transaction.update(doc_ref, {u'frequency': snapshot.get(u'frequency') + 1})
 
def keyword_extraction(event, context):
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
    journal_text = ""
    journal_text_intermediate = ""
    try:
        key_b64_dict = fields_dict['key']
        key_b64 = key_b64_dict['stringValue']
        journal_text_dict = fields_dict['journal_text']
        journal_text_intermediate = journal_text_dict['stringValue']
        journal_text = journal_text_intermediate.replace("’", "\\\\").replace("'", "\\\\")
    except Exception as e:
        print("An error occurred with finding the journal text")
        traceback.print_exc()
    #timestamp_string = timestamp_dict['timestampValue']
    # Converts the timestamp into a 'datetime' object
    #timestamp_datetime = datetime.strptime(timestamp_string, '%Y-%m-%dT%H:%M:%SZ')
    # Checks for profanity and extracts keywords from the journal
    user_ref = db.collection(u'guided_journals').document(user_id)
    try:
        contains_profanity = detect_profanity(journal_text)
        if contains_profanity == True:
            keyword_doc_ref = user_ref.collection(u'daily_journals').document(journal_id)
            data = {'key': firestore.DELETE_FIELD}
            keyword_doc_ref.update(data)
            print("Please revise your guided journal to be more considerate of the workspace and mental health community")
            message = Mail(
                from_email = 'etalreja@hespr.com',
                to_emails = 'vibers-l@hespr.com',
                subject = 'Guided Journal Profanity Alert for ' + user_name,
                html_content = "Hello, Vibers, <br> <br> Hespr's profanity detection algorithm recorded a use of inappropriate language from User <strong>" + str(user_id) + "</strong>, who is registered with a name of <strong>" + user_name + "</strong>. Here's the guided journal entry received by our app: <br> <br> <strong>" + journal_text + "</strong> <br> <br> Sincerely,<br> The Hespr Butterfly"
            )
            sg = SendGridAPIClient(sendgrid_api_key)
            response = sg.send(message)
            # print(response.status_code)
            # print(response.body)
            # print(response.headers)
        else:
            keywordList = finalKeywords(journal_text_intermediate, 10, 10, 10)
            final_keyword_list = []
            user_keyword_list_ref = db.collection(u'users').document(user_id)
            transaction = db.transaction()
            keyword_doc_ref = user_ref.collection(u'daily_journals').document(journal_id)
            try:
                journalBytes = encrypt(journal_text, key_b64)
                journalInfo = {'journal_text': journalBytes, 'key': firestore.DELETE_FIELD, 'journal_last_encrypted': datetime.datetime.now()}
            except Exception as e:
                print("An error occurred encrypting the journal entry")
                journalInfo = {'journal_text': b'Unknown', 'key': firestore.DELETE_FIELD, 'journal_last_encrypted': None}
                traceback.print_exc()
            keyword_doc_ref.update(journalInfo)
            if len(keywordList) < 5:
                for word in keywordList:
                    keyword = word
                    personal_keyword_doc_ref = user_keyword_list_ref.collection(u'personal keyword list').document(keyword)
                    total_keyword_doc_ref = db.collection(u'total_keyword_list').document(keyword)
                    #currentKeywordPolarity = 0
                    try:
                        personal_list = personal_keyword_doc_ref.get().to_dict()
                        personal_entries = personal_list['associated_entries']
                        if journal_id not in personal_entries:
                            personal_entries.append(journal_id)
                    except TypeError:
                        print("No previously associated entries")
                        personal_entries = [journal_id]
                    except Exception as e:
                        print("An error occurred with the discovery of associated entries")
                        print(e)
                        traceback.print_exc()
                    try:
                        personal_keyword_doc_ref.update({u'associated_entries': personal_entries, 'lastUpdated': datetime.datetime.now()})
                        update_frequency_in_transaction(transaction, personal_keyword_doc_ref)
                    except Exception as e:
                        print("First time keyword document creation")
                        print(e)
                        traceback.print_exc()
                        personal_keyword_doc_ref.set({'frequency': 1, 'associated_entries': personal_entries, 'lastUpdated': datetime.datetime.now()})
                    total_entries = []
                    try:
                        total_list = total_keyword_doc_ref.get().to_dict()
                        total_entries = total_list['uidList']
                        if user_id not in total_entries:
                            total_entries.append(user_id)
                    except (TypeError, KeyError):
                        print("No previously associated entries")
                        total_entries = [user_id]
                    except Exception as e:
                        print("An error occurred with the discovery of associated entries for total keyword")
                        print(e)
                        traceback.print_exc()
                    try:
                        total_keyword_doc_ref.update({u'associated_users': total_entries,'lastUpdated': datetime.datetime.now()})
                        update_frequency_in_transaction(transaction, total_keyword_doc_ref)
                    except TypeError:
                        print("First time total keyword document creation")
                        total_keyword_doc_ref.set({'frequency': 1, "uidList": total_entries, 'lastUpdated': datetime.datetime.now()})
                    except Exception as e:
                        total_keyword_doc_ref.set({'frequency': 1, "uidList": total_entries, 'lastUpdated': datetime.datetime.now()})
                        print("An error occurred with updating the total keyword document")
                        print(e)
                        traceback.print_exc()
                    """
                    try:
                        userText = []
                        individualSentimentList = []
                        for entry in personal_entries:
                            specificEntry = user_ref.collection(u'daily_journals').document(entry)
                            specificInfo = specificEntry.get().to_dict()
                            specificText = ""
                            try:
                                specificPreprocessed = specificInfo['journal_text']
                                specificBytes = decrypt(specificPreprocessed, key_b64)
                                specificTextIntermediate = bytes.decode(specificBytes)
                                specificText = specificTextIntermediate.replace("\\\\", "'")
                                specificEntry.update({'journal_last_accessed_in_cloud': datetime.datetime.now()})
                                userText.append(specificText)
                            except Exception as e:
                                print("An error occurred processing the previous journals")
                                print(e)
                                specificEntry.update({'journal_last_accessed_in_cloud': None})
                                traceback.print_exc()
                            try:
                                sentenceList = sentenceFinder(specificText, keyword)
                                weight1 = 0.6
                                multiplier1 = 0.4
                                entryValue = sentimentListAnalysis(sentenceList, weight1, multiplier1)
                                individualSentimentList.append(entryValue)
                            except ValueError:
                                print("No sentence was found with keyword in entry")
                                traceback.print_exc()
                            except Exception as e:
                                print("An unexpected error")
                                traceback.print_exc()
                        weight2 = 0.45
                        multiplier2 = 0.55
                        userValue = 0
                        sentenceValue = 0
                        try:
                            userValue = sentimentListAnalysis(userText, weight2, multiplier2)
                        except Exception as e:
                            print("User Text Analysis Error")
                            traceback.print_exc()
                        try:
                            sentenceValue = listAvgCalculator(individualSentimentList)
                        except ValueError:
                            print("The polarity list of sentences is zero")
                            traceback.print_exc()
                        except Exception as e:
                            print("An unexpected error occurred")
                            traceback.print_exc()
                        weight3 = 0.35
                        multiplier3 = 0.65
                        combinedPolarity = userValue + sentenceValue
                        weightedSum = weight3 * userValue + multiplier3 * sentenceValue
                        finalPolarity = 0
                        if combinedPolarity == 0:
                            finalPolarity = 0
                        else:
                            finalPolarity = weightedSum/combinedPolarity
                        currentKeywordPolarity = finalPolarity
                    except ValueError:
                        print("A list was found to contain no elements in keyword sentiment")
                        traceback.print_exc()
                    except Exception as e:
                        print("An error occurred with the calculation of the keyword sentiment")
                        print(e)
                        traceback.print_exc()
                    try:
                        personal_keyword_doc_ref.update({"Current_Personal_Keyword_Polarity": currentKeywordPolarity, 'polarity_last_updated': datetime.datetime.now()})
                    except Exception as e:
                        print("An error occurred with updating the keyword document")
                        print(e)
                        traceback.print_exc()
                    """
                    final_keyword_list.append(keyword)
            else:
                for i in range(5):
                    keyword = keywordList[i]
                    personal_keyword_doc_ref = user_keyword_list_ref.collection(u'personal keyword list').document(keyword)
                    total_keyword_doc_ref = db.collection(u'total_keyword_list').document(keyword)
                    #currentKeywordPolarity = 0
                    try:
                        personal_list = personal_keyword_doc_ref.get().to_dict()
                        personal_entries = personal_list['associated_entries']
                        if journal_id not in personal_entries:
                            personal_entries.append(journal_id)
                    except TypeError:
                        print("No previously associated entries")
                        personal_entries = [journal_id]
                    except Exception as e:
                        print("An error occurred with the discovery of associated entries")
                        print(e)
                        traceback.print_exc()
                    try:
                        personal_keyword_doc_ref.update({u'associated_entries': personal_entries, 'lastUpdated': datetime.datetime.now()})
                        update_frequency_in_transaction(transaction, personal_keyword_doc_ref)
                    except Exception as e:
                        print("First time keyword document creation")
                        print(e)
                        traceback.print_exc()
                        personal_keyword_doc_ref.set({'frequency': 1, 'associated_entries': personal_entries, 'lastUpdated': datetime.datetime.now()})
                    total_entries = []
                    try:
                        total_list = total_keyword_doc_ref.get().to_dict()
                        total_entries = total_list['uidList']
                        if user_id not in total_entries:
                            total_entries.append(user_id)
                    except (TypeError, KeyError):
                        print("No previously associated entries")
                        total_entries = [user_id]
                    except Exception as e:
                        print("An error occurred with the discovery of associated entries for total keyword")
                        print(e)
                        traceback.print_exc()
                    try:
                        total_keyword_doc_ref.update({u'associated_users': total_entries,'lastUpdated': datetime.datetime.now()})
                        update_frequency_in_transaction(transaction, total_keyword_doc_ref)
                    except TypeError:
                        print("First time total keyword document creation")
                        total_keyword_doc_ref.set({'frequency': 1, "uidList": total_entries, 'lastUpdated': datetime.datetime.now()})
                    except Exception as e:
                        total_keyword_doc_ref.set({'frequency': 1, "uidList": total_entries, 'lastUpdated': datetime.datetime.now()})
                        print("An error occurred with updating the total keyword document")
                        print(e)
                        traceback.print_exc()
                    """
                    try:
                        userText = []
                        individualSentimentList = []
                        for entry in personal_entries:
                            specificEntry = user_ref.collection(u'daily_journals').document(entry)
                            specificInfo = specificEntry.get().to_dict()
                            specificText = ""
                            try:
                                specificPreprocessed = specificInfo['journal_text']
                                specificBytes = decrypt(specificPreprocessed, key_b64)
                                specificText = bytes.decode(specificBytes)
                                specificEntry.update({'journal_last_accessed_in_cloud': datetime.datetime.now()})
                                userText.append(specificText)
                            except Exception as e:
                                print("An error occurred processing the previous journals")
                                print(e)
                                specificEntry.update({'journal_last_accessed_in_cloud': None})
                                traceback.print_exc()
                            try:
                                sentenceList = sentenceFinder(specificText, keyword)
                                weight1 = 0.6
                                multiplier1 = 0.4
                                entryValue = sentimentListAnalysis(sentenceList, weight1, multiplier1)
                                individualSentimentList.append(entryValue)
                            except ValueError:
                                print("No sentence was found with keyword in entry")
                                traceback.print_exc()
                            except Exception as e:
                                print("An unexpected error")
                                traceback.print_exc()
                        weight2 = 0.45
                        multiplier2 = 0.55
                        userValue = 0
                        sentenceValue = 0
                        try:
                            userValue = sentimentListAnalysis(userText, weight2, multiplier2)
                        except Exception as e:
                            print("User Text Analysis Error")
                            traceback.print_exc()
                        try:
                            sentenceValue = listAvgCalculator(individualSentimentList)
                        except ValueError:
                            print("The polarity list of sentences is zero")
                            traceback.print_exc()
                        except Exception as e:
                            print("An unexpected error occurred")
                            traceback.print_exc()
                        weight3 = 0.35
                        multiplier3 = 0.65
                        combinedPolarity = userValue + sentenceValue
                        weightedSum = weight3 * userValue + multiplier3 * sentenceValue
                        finalPolarity = 0
                        if combinedPolarity == 0:
                            finalPolarity = 0
                        else:
                            finalPolarity = weightedSum/combinedPolarity
                        currentKeywordPolarity = finalPolarity
                    except ValueError:
                        print("A list was found to contain no elements in keyword sentiment")
                        traceback.print_exc()
                    except Exception as e:
                        print("An error occurred with the calculation of the keyword sentiment")
                        print(e)
                        traceback.print_exc()
                    try:
                        personal_keyword_doc_ref.update({"Current_Personal_Keyword_Polarity": currentKeywordPolarity, 'polarity_last_updated': datetime.datetime.now()})
                    except Exception as e:
                        print("An error occurred with updating the keyword document")
                        print(e)
                        traceback.print_exc()
                    """
                    final_keyword_list.append(keyword)
            data = { u'personal_keywords': final_keyword_list, u'keywords_generated_timestamp': datetime.datetime.now()}
            keyword_doc_ref.update(data)
            print(final_keyword_list)
    except (TypeError, ValueError):
        user_ref = db.collection(u'guided_journals').document(user_id)
        keyword_doc_ref = user_ref.collection(u'daily_journals').document(journal_id)
        try:
            journalBytes = encrypt(journal_text, key_b64)
            data = {u'personal_keywords': u"Keywords could not be determined", u'keywords_generated_timestamp': None, u'journal_text': journalBytes, 'key': firestore.DELETE_FIELD, u'journal_last_encrypted': datetime.datetime.now()}
        except Exception as e:
            print('An error occurred encrypting the journal')
            traceback.print_exc()
        keyword_doc_ref.update(data)
        print("Please write a more extensive journal entry so that we can more accurately predict your mood!")
        traceback.print_exc()
    except Exception as e:
        print("Sorry, something unexpected occurred. Please contact Hespr Support so that we can investigate the issue for you!")
        print(e)
        traceback.print_exc()
