from google.cloud import firestore
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Establishes the Cloud Firestore client
db = firestore.Client()
# Defines the Sendgrid API credentials
sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')

def detect_reporting(event, context):
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
    # Finds the value associated with the report key (old value)
    old_value_dict = event['oldValue']
    fields_dict1 = old_value_dict['fields']
    report_dict1 = fields_dict1['report']
    report_num_old = report_dict1['integerValue']
    # Finds the value associated with the report key (new value)
    value_dict = event['value']
    fields_dict2 = value_dict['fields']
    report_dict2 = fields_dict2['report']
    report_num_new = report_dict2['integerValue']
    # Finds the user ID
    user_id_dict = fields_dict2['uid']
    user_id = user_id_dict['stringValue']
    # Finds the user name
    name_dict = fields_dict2['nickname']
    name_string = name_dict['stringValue']
    # Finds the post card text
    content_dict = fields_dict2['content']
    content_string = content_dict['stringValue']
    if report_num_new > report_num_old:
         print("A user has reported User " + user_id + " on Hespr's social platform.")
         message = Mail(from_email = 'etalreja@hespr.com', to_emails = 'vibers-l@hespr.com', subject = 'Post Card Report Alert: User ' + user_id, html_content = "Hello, Vibers, <br> <br> Hespr's reporting detection algorithm recorded an increase in the number of reports for User <strong>" + user_id + "</strong>, who is registered with a name of <strong>" + name_string + "</strong>. Here's the text of the post card received by our app: <br> <br> <strong>" + content_string + "</strong> <br> <br> Sincerely,<br> The Hespr Butterfly")
         sg = SendGridAPIClient(sendgrid_api_key)
         response = sg.send(message)
         # sg = SendGridAPIClient(sendgrid_api_key)
         # response = sg.send(message)
    else:
         print("No new reports found!") 
