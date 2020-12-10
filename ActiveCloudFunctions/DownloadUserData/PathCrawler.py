from flask import send_file
from google.cloud import firestore
import os
import json
import base64
import traceback
from collections import defaultdict

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)

# Establishes the Cloud Firestore client
db = firestore.Client()

# Defines the Sendgrid API credentials
sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')

def PathList(top_level_ref, collectionStatus):
    DataDict = {}
    TempDict = {}
    TempDefaultDict = defaultdict(list)
    if collectionStatus == True:
        try:
            collectionDocs = top_level_ref.stream()
            for doc in collectionDocs:
                try:
                    TempDict = PathList(doc.reference, False)
                    for key, value in TempDict.items():
                        TempDefaultDict[key].append(value)
                except:
                    traceback.print_exc()
                    pass
        except:
            traceback.print_exc()
        DataDict = dict(TempDefaultDict)
        return DataDict
    else:
        try:
            DataDict[top_level_ref.parent.id] = {}
            DataDict[top_level_ref.parent.id][top_level_ref.id] = top_level_ref.get().to_dict()
        except:
            traceback.print_exc()
        try:
            subCollections = top_level_ref.collections()
            for collection in subCollections:
                print(collection.id)
                try:
                    TempDict = PathList(collection, True)
                    for key, value in TempDict.items():
                        TempDefaultDict[key].append(value)
                except:
                    traceback.print_exc()
                    pass
        except:
            traceback.print_exc()
        DataDict[top_level_ref.parent.id][top_level_ref.id].update(dict(TempDefaultDict))
        return DataDict
    
def data_retrieval(collectionPaths, documentPaths):
    CumulativeDict = {}
    TempDict = {}
    try:
        for reference in collectionPaths:
            TempDict = PathList(reference, True)
            CumulativeDict = {**CumulativeDict, **TempDict}
    except:
        traceback.print_exc()
    try:
        for reference in documentPaths:
            TempDict = PathList(reference, False)
            CumulativeDict = {**CumulativeDict, **TempDict}
    except:
        traceback.print_exc()
    return CumulativeDict

def send_download_alert(user_name, user_id, user_email, unformattedDict, fileName):
    # Sends an email to notify user about their data
    message = Mail(
        from_email='etalreja@hespr.com', to_emails=user_email,
        subject='Hespr Personal Data Download: ' + user_name,
        html_content="Hey " + user_name + "! <br> <br> Hespr's user account download system would like to inform you that User <strong>" + user_name + "</strong>, has requested to download their account data which has been attached to this email. Thank you for using our app! <br> <br> Sincerely,<br> The Hespr Butterfly"
        )
    writtenDict = json.dumps(unformattedDict, ensure_ascii=False, indent=4, default=str, sort_keys=True)
    encoded = base64.b64encode(writtenDict.encode('utf-8')).decode()
    attachedFile = Attachment(
        FileContent(encoded),
        FileName(fileName),
        FileType('application/txt'),
        Disposition('attachment')
        )
    message.attachment = attachedFile
    sg = SendGridAPIClient(sendgrid_api_key)
    response = sg.send(message)

def send_download_request_info(user_name, user_id, user_email):
    # Sends an email to notify leadership about user data download
    message = Mail(
        from_email='etalreja@hespr.com', to_emails="vibers-l@hespr.com",
        subject='Hespr Personal Data Download: ' + user_id,
        html_content="Hey Vibers! <br> <br> Hespr's user account download system would like to inform you that User <strong>" + user_id + "</strong>, who is registered with a name of <strong>" + user_name + "</strong>, has requested to download their account data which has been processed. <br> <br> Sincerely,<br> The Hespr Butterfly"
        )
    sg = SendGridAPIClient(sendgrid_api_key)
    response = sg.send(message)

def dict_convert_formatted(unformattedDict, fileName):
    absoluteFileName = '/tmp/' + fileName
    with open(absoluteFileName, 'w', encoding='utf-8') as f:
        json.dump(unformattedDict, f, ensure_ascii=False, indent=4, default=str)
    return send_file(absoluteFileName, attachment_filename=absoluteFileName)
        

