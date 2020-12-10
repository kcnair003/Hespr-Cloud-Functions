from flask import send_file
from google.cloud import firestore
import os
import json
import traceback
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
 
def download_data(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()
    request.args = request.args
    if request.args and 'user_id' in request.args:
        return download_user_data("Ethan", request.args.get('user_id'), "etalreja@hespr.com")
    elif request_json and 'user_id' in request_json:
        try:
            uid = request_json['user_id']
            return download_user_data("Ethan", uid, "etalreja@hespr.com")
        except:
            traceback.print_exc()
            return
    else:
        return f'Hello World!'
