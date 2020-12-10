from google.cloud import firestore
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import traceback 

# Establishes the Cloud Firestore client
db = firestore.Client()
# Defines the Sendgrid API credentials
sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')

def send_deletion_alert(user_name, user_id):
    # Sends an email to notify leadership before the deletion process is begun
    message = Mail(from_email = 'etalreja@hespr.com', to_emails = 'vibers-l@hespr.com', subject = 'User Account Deletion Alert: User ' + user_id, html_content = "Hello, Vibers, <br> <br> Hespr's user account deletion system would like to inform you that User <strong>" + user_id + "</strong>, who is registered with a name of <strong>" + user_name + "</strong>, has requested to delete their account which is now waiting for approval within the next 48 hours. <br> <br> Sincerely,<br> The Hespr Butterfly")
    sg = SendGridAPIClient(sendgrid_api_key)
    response = sg.send(message)

def send_deletion_notice(user_name, user_email):
    # Sends an email to notify leadership before the deletion process is begun
    message = Mail(from_email = 'etalreja@hespr.com', to_emails = user_email, subject = 'User Account Deletion Alert: User ' + user_name, html_content = "Hey, " + user_name + "! <br> <br> Hespr's user account deletion system would like to inform you that User <strong>" + user_name + "</strong>, has requested to delete their account which is now waiting for approval within the next 48 hours. Please reach out to us if this request was made in error! <br> <br> Sincerely,<br> The Hespr Butterfly")
    sg = SendGridAPIClient(sendgrid_api_key)
    response = sg.send(message)

def request_user_deletion(event, context):
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
    requested_delete_boolean = user_dict['requested_delete']
    try:
         if requested_delete_boolean == True:
             send_deletion_notice(user_name, user_email)
             send_deletion_alert(user_name, user_id)
         else:
              print('The user has not requested a delete!')
    except Exception as e:
         print('An error occurred with sending the deletion alert')
         traceback.print_exc()