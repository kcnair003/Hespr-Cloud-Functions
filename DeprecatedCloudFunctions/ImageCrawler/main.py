import flickrapi
import urllib
import json
import requests
from google.cloud import storage
from google.cloud import firestore
from firebase import firebase
import firebase_admin
from firebase_admin import db, credentials
import traceback

# Establishes the Cloud Storage and Cloud Firestore clients
storage_client = storage.Client()
firestore_client = firestore.Client()

# Establishes access to the Realtime Database
firebase = firebase.FirebaseApplication('https://hesprmvp.firebaseio.com', None)
default_app = firebase_admin.initialize_app(options={'databaseURL': 'https://hesprmvp.firebaseio.com'})

def outputJSON(keyword):
    #Establishes a second connection with the Flickr API, with an output format set to JSON
    flickr = flickrapi.FlickrAPI('574bd25899d040391568c00d930869ad', 'c4b9ed34b11dbb90', format='json')

    #Performs the photos.search() Flickr API method
    rawJSON = flickr.photos.search(text=keyword, tag_mode='all', tags=keyword, extras='url_c', per_page=4, sort='relevance', safe_search=1)

    #Uses the JSON module to decode the raw output
    output = json.loads(rawJSON.decode('utf-8'))

    #Defines a variable named a, which represents the values of the key named photos
    a = output.get('photos')

    #Defines a variable named photoJSON, which represents the values of the key named photo
    photoJSON = a.get('photo')
    
    return(photoJSON)

def retrieve_image_URLs(photoJSON, keyword):
    image_URL_list = []
    for i in range(4):
        element = photoJSON[i]
        elementKeys = element.keys()
        #Because some images do not have a 'url_c' key, the URLs of these images are found using the farm, server, id, and secret numbers of the images
        if 'url_c' in elementKeys:
            elementURL = element.get('url_c')
        else:
            element['url_c'] = 'https://farm' + str(element['farm']) + '.staticflickr.com/' + element['server'] + '/' + element['id'] + '_' + element['secret'] + '.jpg'
            elementURL = element['url_c']
        image_URL_list.append(elementURL)
    return(image_URL_list)

def upload_images_to_storage(image_URL_list, keyword):
    cloud_storage_bucket = storage_client.bucket('hesprmvp-vcm')
    rtdb_ref = f'/image_urls/{keyword}/'
    # keyword_ref = rtdb_reference.child(f'{keyword}')
    for url in image_URL_list:
        url_index = image_URL_list.index(url)
        image_name = f'{keyword}' + f'{str(url_index + 1)}'
        print(image_name)
        # rtdb_ref = f'/image_urls/{keyword}/{image_name}/'
        # result = firebase.post(rtdb_ref, url)
        result = firebase.put(rtdb_ref, image_name, url)
        print(result) 
        cloud_storage_blob = cloud_storage_bucket.blob(image_name)
        response = requests.get(url)
        needed_content = response.content
        cloud_storage_blob.upload_from_string(needed_content, content_type='image/jpeg')

def crawl_for_images(event, context):
    """Triggered by a change to a Firestore document.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    try:
        resource_string = context.resource
        # print out the resource string that triggered the function
        print(f"Function triggered by change to: {resource_string}.")
        # now print out the entire event object
        print(str(event))
        # Finds the ID of the keyword document and the user ID
        resource_string_list = resource_string.split('/')
        specific_keyword = resource_string_list[6]
        print(specific_keyword)
        json_output = outputJSON(specific_keyword)
        json_output_length = len(json_output)
        if json_output_length == 0:
            total_keyword_list_ref = firestore_client.collection(u'total_keyword_list').document(specific_keyword)
            total_keyword_list_ref.delete()
        image_URLs = retrieve_image_URLs(json_output, specific_keyword)
        for x in image_URLs:
            print(x)
        upload_images_to_storage(image_URLs, specific_keyword)
    except Exception as e:
        traceback.print_exc()
