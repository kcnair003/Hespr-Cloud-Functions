from google.cloud import firestore
import json

# Note: Individual Cloud Firestore documents are the only objects that can act as triggers.
# As a result, this cloud function is triggered by any changes to documents that contain polarity maps.
# The frequency of a keyword in a user's experience can be tracked with the number of times they answer a question with the keyword.

# Establishes access to the Cloud Firestore database
firestore_client = firestore.Client()

def access_user_response_polarities(user_id):
    # print(document_id)
    # print(user_id)
    user_ref = firestore_client.collection(u'guided_journals').document(user_id)
    response_doc_ref = user_ref.collection(u'polarity_logs').order_by(u'time_of_submission')
    response_docs = response_doc_ref.stream()
    response_dict = {}
    user_polarities = []
    for doc in response_docs:
        response_key = doc.id
        stream_output = doc.to_dict()
        chosen_answer_pair = stream_output['chosen_answer']
        chosen_answer_value = chosen_answer_pair.values()
        needed_polarity = float([x for x in chosen_answer_value][0])
        response_dict[response_key] = needed_polarity
        user_polarities.append(needed_polarity)

    # print(user_polarities)
    return(user_polarities)
    # response_doc = response_doc_ref.get()
    # print(f'Document data: {response_doc.to_dict()}')

def strictly_decreasing(L):
    return all(x>y for x, y in zip(L, L[1:]))

def detect_need_for_curated_posts(user_polarities_list):
    min_user_polarity = min(user_polarities_list)
    max_user_polarity = max(user_polarities_list)
    polarity_range = max_user_polarity - min_user_polarity
    # print(polarity_range)
    # Need to confirm with rest of Algorithms team (add non-decreasing and non-increasing as well?)
    if polarity_range >= 0.05 and strictly_decreasing(user_polarities_list) == True:
        needs_grateful_posts = True
        #print(needs_grateful_posts)
        return(needs_grateful_posts)
    else:
        needs_grateful_posts = False
        #print(needs_grateful_posts)
        return(needs_grateful_posts)

def write_need_for_curated_posts(user_id, boolean):
    user_ref = firestore_client.collection(u'guided_journals').document(user_id)
    user_ref.set({'needs_curated_posts': boolean}, merge=True)

def access_curated_posts(user_id):
    grateful_posts_user_ref = firestore_client.collection(u'grateful_posts').document(user_id)
    user_doc = grateful_posts_user_ref.get()
    user_dict = user_doc.to_dict()
    grateful_posts_list = []
    for key in list(user_dict.keys()):
        curated_post_text = user_dict[key]
        if curated_post_text[:4] != 'USED':
            grateful_posts_list.append(curated_post_text)
            new_post = 'USED_' + curated_post_text
            grateful_posts_user_ref.set({key: new_post}, merge=True)
    # print(grateful_posts_list)
    return(grateful_posts_list)  

def fetch_curated_posts(event, context):
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
    document_id_index = len(resource_string_list) - 1
    document_id = resource_string_list[document_id_index]
    user_id = resource_string_list[6]
    output_list = access_user_response_polarities(user_id)
    needs_grateful_posts = detect_need_for_curated_posts(output_list)
    #print(needs_grateful_posts)
    write_need_for_curated_posts(user_id, needs_grateful_posts)
    if needs_grateful_posts == True:
        grateful_posts_final_list = access_curated_posts(user_id)
        for i in grateful_posts_final_list:
            print(i)
    



    