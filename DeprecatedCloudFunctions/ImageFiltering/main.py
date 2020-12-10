import os
import json
import tempfile
from google.cloud import storage, vision
from google.cloud import language_v1
from google.cloud.language_v1 import enums
from wand.image import Image
from firebase import firebase
import firebase_admin
from firebase_admin import db, credentials

# Defines the Cloud Storage and Vision API clients
storageClient = storage.Client()
visionClient = vision.ImageAnnotatorClient()

# Establishes access to the Realtime Database
firebase = firebase.FirebaseApplication('https://hesprmvp.firebaseio.com', None)
default_app = firebase_admin.initialize_app(options={'databaseURL': 'https://hesprmvp.firebaseio.com'})

# References: https://cloud.google.com/functions/docs/tutorials/imagemagick, https://cloud.google.com/vision/docs/detecting-safe-search


def analyzeSentiment(text_phrase):
     # Defines the client, type of document, and the language used in the sentiment analysis
     client = language_v1.LanguageServiceClient()
     type_ = enums.Document.Type.PLAIN_TEXT
     language = "en"
     document = {'content': text_phrase, 'type': type_, 'language': language}
     encodingForm = enums.EncodingType.UTF8
     # Uses the analyze_sentiment() method to find the overall polarity and magnitude of the text
     response = client.analyze_sentiment(document, encoding_type=encodingForm)
     neededPolarity = response.document_sentiment.score
     return(neededPolarity)

def write_labels_and_polarities(outputDict, keyword, image_num):
     ref = f'/keywords/{keyword}/image{str(image_num)}/'
     # Defines the keys of the outputDict dictionary
     outputDict_keys = list(outputDict.keys())
     length_outputDict_keys = len(outputDict_keys)
     # Adds the first five keys to the final_outputDict_keys list
     final_outputDict_keys = []
     if length_outputDict_keys < 5:
          for i in range(length_outputDict_keys):
               final_outputDict_keys.append(outputDict_keys[i])
     else:
          for j in range(5):
               final_outputDict_keys.append(outputDict_keys[j])
     # Defines a list that will contain the label polarities
     label_polarities_list = []

     # Iterates over each label in the dictionary
     for key in final_outputDict_keys:
          # Defines the index of a label, which is used for the path to the realtime database
          needed_label_index = final_outputDict_keys.index(key) + 1
          temp_ref = ref + f'label{str(needed_label_index)}/'
          # Defines the confidence score associated with a label
          value = outputDict[key]

          # Writes the label names and scores to the realtime database
          firebase.put(temp_ref, 'label_name', key)
          firebase.put(temp_ref, 'label_confidence_score', value)

          # Calls the analyzeSentiment() function to find the label polarities
          raw_label_polarity = analyzeSentiment(key)
          firebase.put(temp_ref, 'label_polarity', raw_label_polarity)
          final_label_polarity = raw_label_polarity * value
          label_polarities_list.append(final_label_polarity)

          # Writes the final label polarities to the realtime database
          firebase.put(temp_ref, 'score_polarity_product', final_label_polarity)
     
     return(label_polarities_list)

def find_and_write_image_polarity(polarity_list, keyword, image_num):
     # Defines a variable that will be used to find the sum of the final label polarities
     polarity_sum = 0
     # Iterates over each polarity to find the sum of the polarities
     for polarity in polarity_list:
          polarity_sum += polarity
     # Finds the number of polarities by calculating the length of the list
     num_polarities = len(polarity_list)
     # Calculates the average polarity for the image
     average_image_polarity = (polarity_sum / num_polarities)
     # Writes the average image polarity to the realtime database
     ref = f'/keyword_polarity/{keyword}/images/'
     firebase.put(ref, f'image{str(image_num)}', average_image_polarity)


def filter_images_and_find_labels(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    file = event
    print(f"Processing file: {file['name']}.")
    # Defines the name of the file and the bucket where the file is stored
    img_file = file
    file_name = img_file['name']
    bucket_name = img_file['bucket']
    # Defines variables needed to declare and define the blob
    bucket = storageClient.bucket(bucket_name)
    blob = bucket.get_blob(file_name)
    blob_uri = f'gs://{bucket_name}/{file_name}'
    blob_source = {'source': {'image_uri': blob_uri}}
    # image = vision.types.Image()
    # image.source.image_uri = blob_uri
    # print(blob_uri)
    # Uses the Vision API to find the appropriateness of the image
    api_result = visionClient.safe_search_detection(blob_source)
    api_detection = api_result.safe_search_annotation
    # Defines a dictionary that will be used for the filtering process
    filter_dict = {}
    # Defines strings that represent the results
    likelihood_name = ('UNKNOWN', 'VERY UNLIKELY', 'UNLIKELY', 'POSSIBLE', 'LIKELY', 'VERY LIKELY')
    # Adds the ratings from the safe_search_detection algorithm
    filter_dict['adult'] = api_detection.adult
    filter_dict['spoof'] = api_detection.spoof
    filter_dict['medical'] = api_detection.medical
    filter_dict['violence'] = api_detection.violence
    filter_dict['racy'] = api_detection.racy
    # Defines the keys of the dictionary as elements of a list
    filter_dict_keys = list(filter_dict.keys())
    # Defines the keyword name
    keyword_name = file_name[:-1]
    img_num = int(file_name[-1])
    # Defines the Realtime Database reference
    delete_ref = f'/image_urls/{keyword_name}'
    rtdb_reference = db.reference(delete_ref)
    # Defines a boolean variable that represents if the image is safe
    img_is_appropriate = True
    # Defines a reference for deleted URLs
    deleted_ref = f'/deleted_image_urls/{keyword_name}/{file_name}'
    # Iterates over each rating to check for appropriateness
    for key in filter_dict_keys:
         print(key)
         print(filter_dict[key])
         try:
              if filter_dict[key] > 2:
                   print('This image is not appropriate for use in Hespr!')
                   # Changes the boolean variable
                   img_is_appropriate = False
                   # Accesses the URL of the image from the Realtime Database
                   rtdb_dict = rtdb_reference.get()
                   deleted_img_url = rtdb_dict[file_name]
                   # Adds the deleted URL to the deleted_image_urls node
                   firebase.post(deleted_ref, deleted_img_url)
                   # Removes the image from the respective bucket
                   bucket.delete_blob(file_name)
                   firebase.delete(delete_ref, file_name)
                   break
         except Exception as e:
              print(e)
#     if img_is_appropriate == True:
#          # Prints a message that shows the progress of the algorithm
#          print(f'Labeling {file_name} in {bucket_name}...')
#          image = vision.types.Image()
#          image.source.image_uri = blob_uri
#          # Defines the response generated by the label_detection() method
#          response = visionClient.label_detection(image=image)
#          # Defines the labels of the image
#          labels = response.label_annotations
#          outputDict = {}
#          # Iterates over each label, adding the description and score of each label to a dictionary
#          for label in labels:
#               outputDict[label.description] = label.score
#          print(outputDict)
#          try:
#               label_polarities = write_labels_and_polarities(outputDict, keyword_name, img_num)
#               find_and_write_image_polarity(label_polarities, keyword_name, img_num)
#          except Exception as e:
#               print(e)         
