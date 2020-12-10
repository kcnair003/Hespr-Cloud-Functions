from google.cloud import firestore
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Establishes the Cloud Firestore client
db = firestore.Client()
# Defines the Sendgrid API credentials
sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')

def delete_posts_and_comments(user_id):
    # Deletes any posts associated with the user in the "posts" collection, as well as any comments associated with that post
    posts_ref_docs = db.collection(u'posts').stream()
    for doc in posts_ref_docs:
        doc_dict = doc.to_dict()
        doc_id = doc.id
        needed_user_id = doc_dict['uid']
        if needed_user_id == user_id:
            doc.reference.delete()
            comments_ref_docs = db.collection(u'posts').document(doc_id).collection(u'comments').stream()
            for doc in comments_ref_docs:
                doc.reference.delete()

def delete_guided_journals(user_id):
    # Deletes the user's document in the "guided_journals" collection, as well as any documents in the 'daily_journals' and the 'daily_image_selection' subcollections
    user_journal_ref = db.collection(u'guided_journals').document(user_id)
    journalCollections = user_journal_ref.collections()
    user_journal_ref.delete()
    for collection in journalCollections:
        journal_docs = collection.stream()
        for doc in journal_docs:
            doc.reference.delete()

def send_deletion_alert(user_name, user_id):
    # Sends an email to notify leadership before the deletion process is begun
    message = Mail(from_email = 'etalreja@hespr.com', to_emails = 'vibers-l@hespr.com', subject = 'User Account Deletion Alert: User ' + user_id, html_content = "Hello, Vibers, <br> <br> Hespr's user account deletion system would like to inform you that User <strong>" + user_id + "</strong>, who was registered with a name of <strong>" + user_name + "</strong>, has had their request for account deletion approved and consequently completed. <br> <br> Sincerely,<br> The Hespr Butterfly")
    sg = SendGridAPIClient(sendgrid_api_key)
    response = sg.send(message)

def send_deletion_notice(user_name, user_email):
    # Sends an email to notify leadership before the deletion process is begun
    message = Mail(from_email = 'etalreja@hespr.com', to_emails = user_email, subject = 'User Account Deletion Alert: User ' + user_name, html_content = "Hey, " + user_name + "! <br> <br> Hespr's user account deletion system would like to inform you that User <strong>" + user_name + "</strong>, has had their request for account deletion approved and consequently completed. Thank you for using our platform and we would love to see you back some day! If you have any advice on what you would like for us to add to bring you back, please send us an email! <br> <br> Sincerely,<br> Ethan Talreja, Krishna Nair, Spencer Chubb, and rest of the Hespr team")
    sg = SendGridAPIClient(sendgrid_api_key)
    response = sg.send(message)

def user_deletion(event, context):
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
    resource_string_list = resource_string.split('/')
    # Defines the UID and the nickname of the user
    user_id = resource_string_list[6]
    user_deleted_ref = db.collection(u'users').document(user_id)
    user_dict = user_deleted_ref.get().to_dict()
    user_name = user_dict['nickname']
    user_email = user_dict['email']
    # Accesses a boolean that says whether or not a user requested to delete their account
    approved_deleted_boolean = user_dict['approved_delete']
    if approved_deleted_boolean == True:
        # Deletes the user's document in the "users" collection and the documents within those subcollections
        userCollections = user_deleted_ref.collections()
        user_deleted_ref.delete()
        for collection in userCollections:
            user_sub_docs = collection.stream()
            for doc in user_sub_docs:
                doc.reference.delete()
        # Deletes posts and journals
        delete_posts_and_comments(user_id)
        delete_guided_journals(user_id)
        send_deletion_alert(user_name, user_id)
        send_deletion_notice(user_name, user_email)
    else:
        print("The user's request to delete their account has not been approved!")