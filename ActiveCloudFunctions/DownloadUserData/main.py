from flask import send_file
from google.cloud import firestore
import os
import json
import traceback
import datetime
import sys
sys.path.append('/user_code/PathCrawler.py')
from PathCrawler import PathList, data_retrieval, dict_convert_formatted, send_download_alert, send_download_request_info
from flask import escape

# Establishes the Cloud Firestore client
db = firestore.Client()

def user_document_data_paths(uid):
    documentPaths = [db.collection("users").document(uid), db.collection(u'guided_journals').document(uid)]
    return documentPaths

def user_collection_data_paths(uid):
    collectionPaths = []
    return collectionPaths

def download_user_data(user_name, uid, user_email):
    # Converts user document into json for file send
    finalDict = {}
    finalDict = data_retrieval(user_collection_data_paths(uid), user_document_data_paths(uid))
    # dict_convert_formatted(finalDict, 'user.txt')
    send_download_request_info(user_name, uid, user_email)
    return send_download_alert(user_name, uid, user_email, finalDict, user_name + 'Data.txt')
 
def download_data(event, context):
    """Triggered by a change to a Firestore document.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    resource_string = context.resource
    # print out the resource string that triggered the function
    print(f"Function triggered by change to: {resource_string}.")
    # now print out the entire event object
    print(str(event))
    # Defines the ID of the user
    resource_string_list = resource_string.split('/')
    user_id = resource_string_list[6]
    # Defines the nickname of the user
    user_ref = db.collection(u'users').document(user_id)
    user_dict = user_ref.get().to_dict()
    user_name = user_dict['nickname']
    user_email = user_dict['email']
    # References a boolean that represents a user's request to delete their account
    requested_download_boolean = user_dict['requested_download']
    try:
        if requested_download_boolean == True:
            try:
                user_ref.update({u'requested_download': False, 'lastDownloadedData': datetime.datetime.now()})
            except:
                user_ref.set({u'requested_download': False, 'lastDownloadedData': datetime.datetime.now()})
            return download_user_data(user_name, user_id, user_email)
        else:
              print('The user has not requested to download their information!')
    except Exception as e:
         print('An error occurred with sending the download')
         traceback.print_exc()
