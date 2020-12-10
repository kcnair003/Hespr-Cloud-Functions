import flickrapi
import urllib
import json
import requests
from google.cloud import storage
from firebase import firebase
import firebase_admin
from firebase_admin import db, credentials

# Establishes access to the Realtime Database
firebase = firebase.FirebaseApplication('https://hesprmvp.firebaseio.com', None)
default_app = firebase_admin.initialize_app(options={'databaseURL': 'https://hesprmvp.firebaseio.com'})

# Establishes the Cloud Storage client
storage_client = storage.Client()

def outputJSON(keyword):
    #Establishes a second connection with the Flickr API, with an output format set to JSON
    flickr = flickrapi.FlickrAPI('574bd25899d040391568c00d930869ad', 'c4b9ed34b11dbb90', format='json')

    #Performs the photos.search() Flickr API method
    rawJSON = flickr.photos.search(text=keyword, tag_mode='all', tags=keyword, extras='url_c', per_page=28, sort='relevance', safe_search=1)

    #Uses the JSON module to decode the raw output
    output = json.loads(rawJSON.decode('utf-8'))

    #Defines a variable named a, which represents the values of the key named photos
    a = output.get('photos')

    #Defines a variable named photoJSON, which represents the values of the key named photo
    photoJSON = a.get('photo')
    
    return(photoJSON)

def retrieve_image_URLs(photoJSON, keyword):
    image_URL_list = []
    for i in range(28):
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

def upload_image_to_storage(image_URL, keyword, deleted_img_num):
    cloud_storage_bucket = storage_client.bucket('hesprmvp-vcm')
    cloud_storage_blob = cloud_storage_bucket.blob(f'{keyword}' + f'{deleted_img_num}')
    response = requests.get(image_URL)
    needed_content = response.content
    cloud_storage_blob.upload_from_string(needed_content, content_type='image/jpeg')

def add_images(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    img_file = event
    print(f"Processing file: {img_file['name']}.")
    # Defines the keyword that will be used in the crawler
    img_file_name = img_file['name']
    keyword_name = img_file_name[:-1]
    # Defines the number of the deleted image (string)
    deleted_img_num = img_file_name[-1]
    # Defines a specific reference to the Realtime Database
    rtdb_ref = db.reference(f'/image_urls/{keyword_name}')
    rtdb_dict = rtdb_ref.get()
    rtdb_dict_values = list(rtdb_dict.values())
    # Defines a list of the URLs of the previously deleted images
    deleted_url_list = []
    try:
        deleted_ref = db.reference(f'/deleted_image_urls/{keyword_name}/{img_file_name}')
        deleted_url_dict = deleted_ref.get()
        deleted_url_list = list(deleted_url_dict.values())
    except Exception as e:
        print(e)
    # Calls the needed functions
    json_output = outputJSON(keyword_name)
    img_URL_list = retrieve_image_URLs(json_output, keyword_name)
    # Defines a list for all of the unique URLs (first tier)
    final_img_URL_list = []
    for url in img_URL_list:
        if (url not in rtdb_dict_values) and (url not in deleted_url_list):
            final_img_URL_list.append(url)
    # Finds the first unique url
    unique_url = final_img_URL_list[0]
    # image_name = f'{keyword}' + f'{str(deleted_img_num)}'
    # print(image_name)
    try:
        firebase.put(f'/image_urls/{keyword_name}', img_file_name, unique_url)
    except Exception as e:
        print(e)
    # Uploads the image URL as an image to Cloud Storage
    try:
        upload_image_to_storage(unique_url, keyword_name, deleted_img_num)
    except Exception as e:
        print(e)
    

